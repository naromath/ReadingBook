'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getBookByIsbn } from '@/lib/api';
import type { BrowserMultiFormatReader } from '@zxing/library';

type ZXingModule = typeof import('@zxing/library');

export default function ScanPage() {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const placeholderRef = useRef<HTMLDivElement | null>(null);
  const codeReaderRef = useRef<BrowserMultiFormatReader | null>(null);
  const detectedRef = useRef(false);

  const [status, setStatus] = useState('대기 중: 카메라를 켜면 ISBN을 자동 인식합니다.');
  const [statusType, setStatusType] = useState<'normal' | 'success' | 'error'>('normal');
  const [running, setRunning] = useState(false);

  const updateStatus = (message: string, type: 'normal' | 'success' | 'error' = 'normal') => {
    setStatus(message);
    setStatusType(type);
  };

  const extractIsbn = (rawText: string) => {
    const text = rawText.replace(/[^0-9Xx]/g, '');
    const isbn13Match = text.match(/97[89]\d{10}/);
    if (isbn13Match) return isbn13Match[0];
    const isbn10Match = text.match(/\d{9}[\dXx]/);
    if (isbn10Match) return isbn10Match[0].toUpperCase();
    return null;
  };

  const stopScanning = () => {
    const video = videoRef.current;
    const placeholder = placeholderRef.current;

    if (codeReaderRef.current) {
      codeReaderRef.current.reset();
      codeReaderRef.current = null;
    }

    if (video?.srcObject) {
      const stream = video.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
      video.srcObject = null;
    }

    if (video) video.style.display = 'none';
    if (placeholder) placeholder.style.display = 'flex';
    setRunning(false);
  };

  useEffect(() => {
    return () => stopScanning();
  }, []);

  const startScanning = async () => {
    const video = videoRef.current;
    const placeholder = placeholderRef.current;
    if (!video || !placeholder) return;

    try {
      detectedRef.current = false;
      updateStatus('카메라 준비 중입니다...');
      setRunning(true);

      const ZXing: ZXingModule = await import('@zxing/library');
      const hints = new Map();
      hints.set(ZXing.DecodeHintType.POSSIBLE_FORMATS, [
        ZXing.BarcodeFormat.EAN_13,
        ZXing.BarcodeFormat.EAN_8,
        ZXing.BarcodeFormat.UPC_A,
        ZXing.BarcodeFormat.CODE_128
      ]);

      const codeReader = new ZXing.BrowserMultiFormatReader(hints, 300);
      codeReaderRef.current = codeReader;

      const devices = await codeReader.listVideoInputDevices();
      if (!devices.length) {
        throw new Error('사용 가능한 카메라가 없습니다.');
      }

      const backCamera = devices.find((device) => /back|rear|environment/i.test(device.label));
      const selectedDeviceId = (backCamera || devices[0]).deviceId;

      void codeReader.decodeFromVideoDevice(selectedDeviceId, video, async (result, error) => {
        if (detectedRef.current) return;

        if (result) {
          const rawCode = result.getText();
          const isbn = extractIsbn(rawCode);

          if (!isbn) {
            updateStatus(`바코드(${rawCode})는 읽었지만 ISBN 형식이 아닙니다.`, 'error');
            return;
          }

          detectedRef.current = true;
          if (navigator.vibrate) navigator.vibrate(120);
          updateStatus(`ISBN 인식 성공: ${isbn} / 알라딘에서 조회 중입니다...`);

          try {
            const response = await getBookByIsbn(isbn);
            const book = response.data;
            const author = book.authors?.[0] || '저자 정보 없음';
            updateStatus(`조회 완료: "${book.title}" / ${author}`, 'success');
          } catch (e) {
            const message = e instanceof Error ? e.message : '알라딘 조회에 실패했습니다.';
            updateStatus(`알라딘 조회 실패(${message}) - 검색 페이지에서 확인해 주세요.`, 'error');
          } finally {
            stopScanning();
            setTimeout(() => {
              router.push(`/search?q=${encodeURIComponent(isbn)}&query_type=ISBN13`);
            }, 800);
          }
          return;
        }

        if (error && !(error instanceof ZXing.NotFoundException)) {
          updateStatus(`스캔 중 오류: ${String(error)}`, 'error');
        }
      });

      video.style.display = 'block';
      placeholder.style.display = 'none';
      updateStatus('스캔 중: 바코드를 중앙 가이드에 0.5초 이상 고정해 주세요.');
    } catch (e) {
      const message = e instanceof Error ? e.message : '카메라 시작에 실패했습니다.';
      stopScanning();
      updateStatus(`카메라 시작 실패: ${message}`, 'error');
    }
  };

  const statusClass = statusType === 'success' ? 'status-panel success' : statusType === 'error' ? 'status-panel error' : 'status-panel';

  return (
    <section className="hero-panel compact">
      <div className="section-row">
        <h1 className="hero-title">ISBN Scanner</h1>
        <button type="button" className="ghost-btn" onClick={() => router.push('/search')}>Manual Search</button>
      </div>
      <p className="muted-copy">스마트폰 후면 카메라로 책 뒷면 바코드를 비춰 주세요.</p>

      <div id="camera-container">
        <video id="video" ref={videoRef} autoPlay playsInline muted style={{ display: 'none' }} />
        <div id="camera-placeholder" className="camera-placeholder" ref={placeholderRef}>
          카메라를 켜고 바코드를 중앙 가이드에 맞춰 주세요.
        </div>
        <div className="scan-focus-box" aria-hidden="true" />
      </div>

      <div className="scan-controls">
        <button type="button" className="btn-primary-solid" onClick={startScanning} disabled={running}>카메라 켜기</button>
        <button type="button" className="btn-soft" onClick={stopScanning} disabled={!running}>중지</button>
      </div>

      <div className={statusClass}>{status}</div>
    </section>
  );
}

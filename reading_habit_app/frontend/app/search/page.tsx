'use client';

import { FormEvent, Suspense, useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { registerBook, searchBook } from '@/lib/api';
import type { BookData, QueryType } from '@/types';

const GOALS = ['투자', '자기개발', '경영', '건강', '기타'];

function SearchPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const qFromUrl = searchParams.get('q') || '';
  const typeFromUrl = (searchParams.get('query_type') || 'Title') as QueryType;

  const initialType = useMemo<QueryType>(() => {
    return ['Title', 'Author', 'ISBN13'].includes(typeFromUrl) ? typeFromUrl : 'Title';
  }, [typeFromUrl]);

  const [query, setQuery] = useState(qFromUrl);
  const [queryType, setQueryType] = useState<QueryType>(initialType);
  const [userGoal, setUserGoal] = useState('');
  const [bookData, setBookData] = useState<BookData | null>(null);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setQuery(qFromUrl);
    setQueryType(initialType);
  }, [qFromUrl, initialType]);

  useEffect(() => {
    const run = async () => {
      if (!qFromUrl) return;
      setLoadingSearch(true);
      setError('');
      setMessage('');
      try {
        const response = await searchBook(qFromUrl, initialType);
        setBookData(response.data.book_data);
        setMessage('검색 결과를 확인했습니다. 독서 목적을 선택 후 등록해 주세요.');
      } catch (e) {
        const messageText = e instanceof Error ? e.message : '검색에 실패했습니다.';
        setError(messageText);
        setBookData(null);
      } finally {
        setLoadingSearch(false);
      }
    };

    run();
  }, [qFromUrl, initialType]);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!query.trim()) {
      setError('검색어를 입력해 주세요.');
      return;
    }
    if (!userGoal) {
      setError('독서 목적을 선택해 주세요.');
      return;
    }

    setSubmitting(true);
    setError('');
    setMessage('');

    try {
      await registerBook(query.trim(), queryType, userGoal);
      setMessage('책 등록과 AI 큐레이션이 완료되었습니다.');
      router.push('/log');
    } catch (e) {
      const messageText = e instanceof Error ? e.message : '책 등록에 실패했습니다.';
      setError(messageText);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="hero-panel compact">
      <div className="section-row">
        <h1 className="hero-title">Search & Register</h1>
        <button type="button" className="ghost-btn" onClick={() => router.push('/scan')}>Scan ISBN</button>
      </div>

      <p className="muted-copy">제목, 저자, ISBN으로 검색하고 독서 목표를 설정하면 바로 큐레이션이 생성됩니다.</p>

      {loadingSearch ? <p className="loading-text">알라딘 API 조회 중...</p> : null}
      {message ? <div className="message-box">{message}</div> : null}
      {error ? <div className="message-box error">{error}</div> : null}

      {bookData ? (
        <article className="result-card">
          {bookData.thumbnail ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={bookData.thumbnail} className="result-cover" alt={bookData.title} />
          ) : null}
          <div>
            <span className="pill">Aladin API</span>
            <h3>{bookData.title}</h3>
            <p>{bookData.authors?.[0] || '저자 정보 없음'}</p>
            <p className="muted-copy">
              총 {bookData.page_count}쪽 {bookData.isbn13 ? `· ISBN13 ${bookData.isbn13}` : ''}
            </p>
          </div>
        </article>
      ) : null}

      <form onSubmit={onSubmit} className="stack-form">
        <div className="form-line radio-group">
          <label className="radio-option"><input type="radio" name="query_type" value="Title" checked={queryType === 'Title'} onChange={() => setQueryType('Title')} /> 제목</label>
          <label className="radio-option"><input type="radio" name="query_type" value="Author" checked={queryType === 'Author'} onChange={() => setQueryType('Author')} /> 저자</label>
          <label className="radio-option"><input type="radio" name="query_type" value="ISBN13" checked={queryType === 'ISBN13'} onChange={() => setQueryType('ISBN13')} /> ISBN</label>
        </div>

        <div className="form-grid two">
          <div>
            <label htmlFor="query" className="label">검색어</label>
            <input
              id="query"
              type="text"
              inputMode={queryType === 'ISBN13' ? 'numeric' : undefined}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={queryType === 'ISBN13' ? 'ISBN 숫자를 입력해 주세요' : '검색어를 입력해 주세요'}
              required
            />
          </div>
          <div>
            <label htmlFor="goal" className="label">독서 목적</label>
            <select id="goal" value={userGoal} onChange={(event) => setUserGoal(event.target.value)} required>
              <option value="" disabled>목적을 선택해 주세요</option>
              {GOALS.map((goal) => (
                <option key={goal} value={goal}>{goal}</option>
              ))}
            </select>
          </div>
        </div>

        <button type="submit" className="btn-primary-solid" disabled={submitting}>
          {submitting ? '등록 중...' : '책 정보 불러오기'}
        </button>
      </form>
    </section>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<section className="content-card"><p className="loading-text">검색 화면을 준비 중...</p></section>}>
      <SearchPageContent />
    </Suspense>
  );
}

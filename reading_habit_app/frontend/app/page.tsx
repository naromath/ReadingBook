'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getHome } from '@/lib/api';
import type { BookshelfBook, BookData, QueryType } from '@/types';

export default function DiscoverPage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [queryType, setQueryType] = useState<QueryType>('Title');
  const [allBooks, setAllBooks] = useState<BookshelfBook[]>([]);
  const [currentBook, setCurrentBook] = useState<BookData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      try {
        const response = await getHome();
        setAllBooks(response.data.all_books || []);
        setCurrentBook(response.data.current_book || null);
      } catch (e) {
        const message = e instanceof Error ? e.message : '홈 정보를 불러오지 못했습니다.';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    run();
  }, []);

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!query.trim()) {
      router.push('/search');
      return;
    }
    const q = encodeURIComponent(query.trim());
    router.push(`/search?q=${q}&query_type=${queryType}`);
  };

  return (
    <>
      <section className="hero-panel">
        <h1 className="hero-title">Discover</h1>

        <form className="discover-search" onSubmit={onSubmit}>
          <select
            className="search-select"
            value={queryType}
            onChange={(event) => setQueryType(event.target.value as QueryType)}
            aria-label="search type"
          >
            <option value="Title">All Categories</option>
            <option value="Author">Author</option>
            <option value="ISBN13">ISBN</option>
          </select>
          <input
            type="text"
            className="search-input"
            placeholder="find the book you like...."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button type="submit" className="search-btn">Search</button>
        </form>

        <div className="section-row">
          <h2>Book Recommendation</h2>
          <button type="button" className="ghost-btn" onClick={() => router.push('/bookshelf')}>
            View all
          </button>
        </div>

        {loading ? <p className="loading-text">책 목록을 불러오는 중...</p> : null}
        {error ? <div className="message-box error">{error}</div> : null}

        <div className="book-row">
          {allBooks.length > 0 ? (
            allBooks.slice(0, 6).map((book) => (
              <article className="book-tile" key={`${book.book_title}-${book.last_read || ''}`}>
                <div className="cover-slot">
                  {book.book_image ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img className="cover-img" src={book.book_image} alt={book.book_title} />
                  ) : (
                    <div className="no-cover">NO COVER</div>
                  )}
                </div>
                <h3>{book.book_title}</h3>
              </article>
            ))
          ) : (
            <>
              <article className="book-tile placeholder"><div className="cover-slot" /><h3>The Psychology of Money</h3></article>
              <article className="book-tile placeholder"><div className="cover-slot" /><h3>Company of One</h3></article>
              <article className="book-tile placeholder"><div className="cover-slot" /><h3>How Innovation Works</h3></article>
              <article className="book-tile placeholder"><div className="cover-slot" /><h3>The Picture of Dorian Gray</h3></article>
            </>
          )}
        </div>
      </section>

      <section className="content-card">
        <div className="section-row">
          <h2>Book Category</h2>
          <button type="button" className="ghost-icon" onClick={() => router.push('/search')}>◫</button>
        </div>

        <div className="category-grid">
          <article className="category-card mint"><div className="category-cover" /><h3>Money/Investing</h3></article>
          <article className="category-card sand"><div className="category-cover" /><h3>Design</h3></article>
          <article className="category-card blue"><div className="category-cover" /><h3>Business</h3></article>
          <article className="category-card coral"><div className="category-cover" /><h3>Self Improvement</h3></article>
        </div>

        {currentBook ? (
          <div className="focus-book">
            <span>Now reading</span>
            <strong>{currentBook.title}</strong>
          </div>
        ) : null}
      </section>
    </>
  );
}

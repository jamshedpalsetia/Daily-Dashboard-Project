interface Props {
  symbol: string;
}

/** Opens the quote page on Yahoo Finance, which is where the prices come from. */
export function TickerLink({ symbol }: Props) {
  return (
    <a
      className="ticker"
      href={`https://finance.yahoo.com/quote/${encodeURIComponent(symbol)}`}
      target="_blank"
      rel="noreferrer"
      title={`${symbol} details on Yahoo Finance`}
    >
      {symbol}
    </a>
  );
}

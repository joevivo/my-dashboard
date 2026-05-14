import React, { useEffect, useMemo, useState } from "react";

const startingHoldings = [
  { account: "JV401K", ticker: "CGDV", shares: 424 },
  { account: "JV401K", ticker: "FTHI", shares: 1073 },
  { account: "JV401K", ticker: "FTCB", shares: 1411 },
  { account: "JV401K", ticker: "LGOV", shares: 1183 },
  { account: "JV401K", ticker: "LMBS", shares: 513 },
  { account: "JV401K", ticker: "CIBR", shares: 103 },
  { account: "JV401K", ticker: "GRID", shares: 36 },
  { account: "JV401K", ticker: "FPE", shares: 1425 },
  { account: "JV401K", ticker: "AIRR", shares: 55 },
  { account: "JV401K", ticker: "SDVY", shares: 474 },
  { account: "JV401K", ticker: "SCI", shares: 1436 },
  { account: "JV401K", ticker: "HYGV", shares: 799 },
  { account: "JV401K", ticker: "IQDF", shares: 292 },
  { account: "JV401K", ticker: "RAVI", shares: 386 },
  { account: "JV401K", ticker: "QLC", shares: 75 },
  { account: "JV401K", ticker: "LVHI", shares: 246 },
  { account: "JV401K", ticker: "BUFR", shares: 2743 },
  { account: "JV401K", ticker: "QMNV", shares: 217 },
  { account: "JV401K", ticker: "QQQ", shares: 29 },
  { account: "JV401K", ticker: "BINC", shares: 617 },
  { account: "JV401K", ticker: "PVAL", shares: 406 },
  { account: "JV401K", ticker: "SMH", shares: 13 },
  { account: "JV401K", ticker: "VCIT", shares: 306 },
    { account: "MV401K", ticker: "CGDV", shares: 153 },
  { account: "MV401K", ticker: "FTHI", shares: 554 },
  { account: "MV401K", ticker: "FTCB", shares: 711 },
  { account: "MV401K", ticker: "LGOV", shares: 599 },
  { account: "MV401K", ticker: "LMBS", shares: 260 },
  { account: "MV401K", ticker: "CIBR", shares: 58 },
  { account: "MV401K", ticker: "GRID", shares: 23 },
  { account: "MV401K", ticker: "FPE", shares: 723 },
  { account: "MV401K", ticker: "AIRR", shares: 33 },
  { account: "MV401K", ticker: "SDVY", shares: 159 },
  { account: "MV401K", ticker: "SCIO", shares: 724 },
  { account: "MV401K", ticker: "HYGV", shares: 284 },
  { account: "MV401K", ticker: "TDTT", shares: 186 },
  { account: "MV401K", ticker: "IQDF", shares: 193 },
  { account: "MV401K", ticker: "RAVI", shares: 47 },
  { account: "MV401K", ticker: "QLC", shares: 38 },
  { account: "MV401K", ticker: "LVHI", shares: 168 },
  { account: "MV401K", ticker: "BUFR", shares: 1401 },
  { account: "MV401K", ticker: "QMNV", shares: 108 },
  { account: "MV401K", ticker: "QQQ", shares: 11 },
  { account: "MV401K", ticker: "BINC", shares: 243 },
  { account: "MV401K", ticker: "PVAL", shares: 136 },
  { account: "MV401K", ticker: "SMH", shares: 9 },
  { account: "MV401K", ticker: "VCIT", shares: 155 },
  { account: "MV401K", ticker: "VOO", shares: 10 },
  { account: "Vanguard ROTH IRA", ticker: "VV", shares: 19.008 },
  { account: "Vanguard ROTH IRA", ticker: "VMFXX", shares: 3661 },
  { account: "IBKR", ticker: "AAPL", shares: 101.45 },
  { account: "IBKR", ticker: "AKAM", shares: 118.9 },
  { account: "IBKR", ticker: "CRM", shares: 55.95 },
  { account: "IBKR", ticker: "MKC", shares: 122.55 },
  { account: "IBKR", ticker: "PANW", shares: 270 },
  { account: "IBKR", ticker: "SBUX", shares: 126.99 },
  { account: "IBKR", ticker: "USB", shares: 92.29 },
  { account: "Tmobile Stock", ticker: "TMUS", shares: 143 },
  {
    account: "ROTH IRA (2016 - )",
    ticker: "CASH",
    assetName: "Money Market",
    shares: 183739,
  },
  { account: "TMO 401K", ticker: "TMUS", shares: 169.413 },
];

const API_BASE = "http://localhost:4000";

const tickerTapeItems = [
  { symbol: "AAPL", label: "Apple" },
  { symbol: "AKAM", label: "Akamai" },
  { symbol: "CRM", label: "Salesforce" },
  { symbol: "MKC", label: "McCormick" },
  { symbol: "PANW", label: "Palo Alto" },
  { symbol: "SBUX", label: "Starbucks" },
  { symbol: "USB", label: "U.S. Bank" },
  { symbol: "TMUS", label: "T-Mobile" },
  { symbol: "DIA", label: "Dow" },
  { symbol: "SPY", label: "S&P 500" },
  { symbol: "QQQ", label: "Nasdaq" },
];

const tickerTapeSymbols = tickerTapeItems.map((item) => item.symbol);

const normalizeHoldingAccounts = (holdings) => {
  return holdings.map((holding) => {
    if (holding.account === "Vanguard 1" || holding.account === "Vanguard 2") {
      return {
        ...holding,
        account: "Vanguard ROTH IRA",
      };
    }

    return holding;
  });
};

export default function FinanceView() {
  const [holdings, setHoldings] = useState(() => {
    const saved = localStorage.getItem("portfolioHoldings");

    if (saved) {
      const normalized = normalizeHoldingAccounts(JSON.parse(saved));
      localStorage.setItem("portfolioHoldings", JSON.stringify(normalized));
      return normalized;
    }

    return startingHoldings;
  });

  const [quotes, setQuotes] = useState({});
  const [quoteStatus, setQuoteStatus] = useState("idle");
  const [quoteError, setQuoteError] = useState("");
  const [account, setAccount] = useState("");
  const [ticker, setTicker] = useState("");
  const [shares, setShares] = useState("");

  const symbols = useMemo(() => {
    return [
      ...new Set([
        ...holdings
          .map((holding) => holding.ticker.toUpperCase())
          .filter((tickerSymbol) => tickerSymbol !== "CASH"),
        ...tickerTapeSymbols,
      ]),
    ];
  }, [holdings]);

  const groupedAccounts = useMemo(() => {
    return holdings.reduce((groups, holding) => {
      if (!groups[holding.account]) groups[holding.account] = [];
      groups[holding.account].push(holding);
      return groups;
    }, {});
  }, [holdings]);

  const getQuote = (tickerSymbol) => {
    if (tickerSymbol.toUpperCase() === "CASH") {
      return {
        symbol: "CASH",
        price: 1,
        previousClose: 1,
        change: 0,
        changePercent: 0,
        high: 1,
        low: 1,
        open: 1,
        timestamp: null,
        error: null,
      };
    }

    return quotes[tickerSymbol.toUpperCase()] || null;
  };

  const getHoldingValue = (holding) => {
    const quote = getQuote(holding.ticker);
    if (!quote?.price) return null;
    return holding.shares * quote.price;
  };

  const getHoldingDailyChange = (holding) => {
    const quote = getQuote(holding.ticker);
    if (quote?.change == null) return null;
    return holding.shares * quote.change;
  };

  const accountSummaries = useMemo(() => {
    return Object.entries(groupedAccounts).map(([accountName, accountHoldings]) => {
      const value = accountHoldings.reduce(
        (sum, holding) => sum + (getHoldingValue(holding) || 0),
        0
      );

      const dailyChange = accountHoldings.reduce(
        (sum, holding) => sum + (getHoldingDailyChange(holding) || 0),
        0
      );

      const pricedHoldings = accountHoldings.filter(
        (holding) => getHoldingValue(holding) !== null
      ).length;

      return {
        accountName,
        count: accountHoldings.length,
        value,
        dailyChange,
        pricedHoldings,
        hasAnyPrices: pricedHoldings > 0,
      };
    });
  }, [groupedAccounts, quotes]);

  const portfolioValue = accountSummaries.reduce((sum, item) => sum + item.value, 0);
  const portfolioDailyChange = accountSummaries.reduce((sum, item) => sum + item.dailyChange, 0);
  const portfolioDailyPercent =
    portfolioValue - portfolioDailyChange
      ? (portfolioDailyChange / (portfolioValue - portfolioDailyChange)) * 100
      : 0;

  const pricedHoldingsCount = holdings.filter(
    (holding) => getHoldingValue(holding) !== null
  ).length;

  const saveHoldings = (nextHoldings) => {
    setHoldings(nextHoldings);
    localStorage.setItem("portfolioHoldings", JSON.stringify(nextHoldings));
  };

  const fetchQuotes = async () => {
    if (!symbols.length) return;

    try {
      setQuoteStatus("loading");
      setQuoteError("");

      const response = await fetch(`${API_BASE}/api/quotes?symbols=${symbols.join(",")}`);

      if (!response.ok) {
        throw new Error(`Quote request failed: ${response.status}`);
      }

      const data = await response.json();
      const nextQuotes = {};

      (data.quotes || []).forEach((quote) => {
        nextQuotes[quote.symbol] = quote;
      });

      setQuotes(nextQuotes);
      setQuoteStatus("loaded");
    } catch (error) {
      console.error("Quote fetch error:", error);
      setQuoteError("Unable to load quotes. Make sure backend is running.");
      setQuoteStatus("error");
    }
  };

  useEffect(() => {
    fetchQuotes();
  }, [symbols.join(",")]);

  const addHolding = () => {
    if (!account.trim() || !ticker.trim() || !shares) return;

    saveHoldings([
      ...holdings,
      {
        account: account.trim(),
        ticker: ticker.trim().toUpperCase(),
        shares: Number(shares),
      },
    ]);

    setAccount("");
    setTicker("");
    setShares("");
  };

  const deleteHolding = (indexToDelete) => {
    saveHoldings(holdings.filter((_, index) => index !== indexToDelete));
  };

  const resetToStartingHoldings = () => {
    saveHoldings(startingHoldings);
  };

  const formatCurrency = (value) => {
    if (value == null || Number.isNaN(value)) return "Pending";

    return value.toLocaleString(undefined, {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    });
  };

  const formatPercent = (value) => {
    if (value == null || Number.isNaN(value)) return "Pending";
    return `${value.toFixed(2)}%`;
  };

  const formatNumber = (value) => {
    return value.toLocaleString(undefined, {
      maximumFractionDigits: 3,
    });
  };

  const changeClass = (value) => {
    if (value > 0) return "text-green-700";
    if (value < 0) return "text-red-700";
    return "text-slate-500";
  };

  return (
    <div className="space-y-5">
      <div className="dashboard-panel p-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold mb-2">Finance</h1>
            <p className="text-sm text-slate-500">
              Portfolio holdings by account with live quote values from Finnhub via your backend.
            </p>
          </div>

          <button
            onClick={fetchQuotes}
            className="bg-slate-900 hover:bg-slate-800 transition text-white px-4 py-2 rounded-lg text-sm"
          >
            Refresh Quotes
          </button>
        </div>

        {quoteStatus === "loading" && (
          <p className="text-sm text-slate-500 mt-3">Loading quotes...</p>
        )}

        {quoteError && <p className="text-sm text-red-600 mt-3">{quoteError}</p>}
      </div>

      <TickerTape items={tickerTapeItems} getQuote={getQuote} formatCurrency={formatCurrency} formatPercent={formatPercent} changeClass={changeClass} />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard
          label="Portfolio Value"
          value={pricedHoldingsCount ? formatCurrency(portfolioValue) : "Pricing pending"}
        />

        <SummaryCard
          label="Daily Change"
          value={pricedHoldingsCount ? formatCurrency(portfolioDailyChange) : "Pricing pending"}
          valueClass={changeClass(portfolioDailyChange)}
        />

        <SummaryCard
          label="Daily %"
          value={pricedHoldingsCount ? formatPercent(portfolioDailyPercent) : "Pricing pending"}
          valueClass={changeClass(portfolioDailyPercent)}
        />

        <SummaryCard label="Priced Holdings" value={`${pricedHoldingsCount}/${holdings.length}`} />
      </div>

      <div className="space-y-3">
        {Object.entries(groupedAccounts).map(([accountName, accountHoldings]) => {
          const summary = accountSummaries.find((item) => item.accountName === accountName);

          const accountDailyPercent =
            summary?.value - summary?.dailyChange
              ? (summary.dailyChange / (summary.value - summary.dailyChange)) * 100
              : 0;

          return (
            <details
              key={accountName}
              className="dashboard-panel overflow-hidden"
            >
              <summary className="cursor-pointer p-5 list-none">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                  <div>
                    <div className="text-xl font-bold">{accountName}</div>
                    <div className="text-sm text-slate-500">
                      {accountHoldings.length} holdings · {summary?.pricedHoldings || 0} priced
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-left md:text-right">
                    <MiniMetric
                      label="Account Value"
                      value={summary?.hasAnyPrices ? formatCurrency(summary.value) : "Pricing pending"}
                    />

                    <MiniMetric
                      label="Daily Change"
                      value={summary?.hasAnyPrices ? formatCurrency(summary.dailyChange) : "Pricing pending"}
                      valueClass={changeClass(summary?.dailyChange || 0)}
                    />

                    <MiniMetric
                      label="Daily %"
                      value={summary?.hasAnyPrices ? formatPercent(accountDailyPercent) : "Pricing pending"}
                      valueClass={changeClass(accountDailyPercent)}
                    />
                  </div>
                </div>
              </summary>

              <div className="px-5 pb-5">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-100/80 text-slate-700">
                      <tr>
                        <th className="text-left p-3 border-b border-slate-200/70">Ticker</th>
                        <th className="text-right p-3 border-b border-slate-200/70">Shares</th>
                        <th className="text-right p-3 border-b border-slate-200/70">Price</th>
                        <th className="text-right p-3 border-b border-slate-200/70">Daily $</th>
                        <th className="text-right p-3 border-b border-slate-200/70">Daily %</th>
                        <th className="text-right p-3 border-b border-slate-200/70">Value</th>
                        <th className="text-left p-3 border-b border-slate-200/70">Action</th>
                      </tr>
                    </thead>

                    <tbody>
                      {accountHoldings.map((holding, localIndex) => {
                        const globalIndex = holdings.findIndex(
                          (item) =>
                            item.account === holding.account &&
                            item.ticker === holding.ticker &&
                            item.shares === holding.shares
                        );

                        const quote = getQuote(holding.ticker);
                        const value = getHoldingValue(holding);
                        const dailyChange = getHoldingDailyChange(holding);

                        return (
                          <tr key={`${holding.account}-${holding.ticker}-${localIndex}`}>
                            <td className="p-3 border-b border-slate-200/70 font-semibold">
                              {holding.assetName || holding.ticker}
                              {holding.assetName && (
                                <div className="text-xs text-slate-500">
                                  {holding.ticker}
                                </div>
                              )}
                              {quote?.error && (
                                <div className="text-xs text-red-600">Quote unavailable</div>
                              )}
                            </td>

                            <td className="p-3 border-b border-slate-200/70 text-right">{formatNumber(holding.shares)}</td>
                            <td className="p-3 border-b border-slate-200/70 text-right">
                              {quote?.price ? formatCurrency(quote.price) : "Pending"}
                            </td>

                            <td className={`p-3 border-b border-slate-200/70 text-right ${changeClass(dailyChange || 0)}`}>
                              {dailyChange != null ? formatCurrency(dailyChange) : "Pending"}
                            </td>

                            <td className={`p-3 border-b border-slate-200/70 text-right ${changeClass(quote?.changePercent || 0)}`}>
                              {quote?.changePercent != null ? formatPercent(quote.changePercent) : "Pending"}
                            </td>

                            <td className="p-3 border-b border-slate-200/70 text-right font-semibold">
                              {value != null ? formatCurrency(value) : "Pending"}
                            </td>

                            <td className="p-3 border-b border-slate-200/70">
                              <button
                                onClick={() => deleteHolding(globalIndex)}
                                className="text-red-600 hover:text-red-700 hover:underline text-sm"
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </details>
          );
        })}
      </div>

      <div className="dashboard-panel p-6">
        <h2 className="text-xl font-bold mb-4">Add Holding</h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            value={account}
            onChange={(e) => setAccount(e.target.value)}
            placeholder="Account"
            className="border border-slate-200 bg-white/80 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-slate-300"
          />

          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="Ticker"
            className="border border-slate-200 bg-white/80 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-slate-300"
          />

          <input
            value={shares}
            onChange={(e) => setShares(e.target.value)}
            placeholder="Shares"
            type="number"
            step="0.001"
            className="border border-slate-200 bg-white/80 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-slate-300"
          />

          <button onClick={addHolding} className="bg-slate-900 hover:bg-slate-800 transition text-white px-4 py-2 rounded-lg">
            Add Holding
          </button>
        </div>

        <button
          onClick={resetToStartingHoldings}
          className="mt-3 bg-slate-200 hover:bg-slate-300 transition text-slate-800 px-4 py-2 rounded-lg text-sm"
        >
          Reset to Starting Holdings
        </button>
      </div>
    </div>
  );
}


function TickerTape({ items, getQuote, formatCurrency, formatPercent, changeClass }) {
  const renderedItems = [...items, ...items];

  return (
    <div className="dashboard-panel overflow-hidden">
      <div className="flex items-center border-b border-slate-200/70 px-5 py-3">
        <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold">
          Market Tape
        </div>
      </div>

      <div className="relative overflow-hidden py-3">
        <div className="ticker-track flex gap-6 whitespace-nowrap">
          {renderedItems.map((item, index) => {
            const quote = getQuote(item.symbol);
            const changePercent = quote?.changePercent ?? null;

            return (
              <div
                key={`${item.symbol}-${index}`}
                className="inline-flex items-center gap-2 text-sm"
              >
                <span className="font-semibold text-slate-900">
                  {item.label}
                </span>

                <span className="text-xs text-slate-400">
                  {item.symbol}
                </span>

                <span className="tabular-nums text-slate-700">
                  {quote?.price ? formatCurrency(quote.price) : "Pending"}
                </span>

                <span className={`tabular-nums ${changeClass(changePercent || 0)}`}>
                  {changePercent != null ? formatPercent(changePercent) : ""}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, valueClass = "" }) {
  return (
    <div className="dashboard-panel p-5">
      <div className="text-xs uppercase text-slate-500">{label}</div>
      <div className={`text-2xl font-semibold tracking-tight mt-1 ${valueClass}`}>{value}</div>
    </div>
  );
}

function MiniMetric({ label, value, valueClass = "" }) {
  return (
    <div>
      <div className="text-xs uppercase text-slate-500">{label}</div>
      <div className={`text-lg font-semibold tracking-tight ${valueClass}`}>{value}</div>
    </div>
  );
}

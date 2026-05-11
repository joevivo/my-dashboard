import React, { useMemo, useState } from "react";

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
  { account: "Vanguard 1", ticker: "VV", shares: 19.008 },
  { account: "Vanguard 2", ticker: "VMFXX", shares: 3661 },
];

export default function FinanceView() {
  const [holdings, setHoldings] = useState(() => {
    const saved = localStorage.getItem("portfolioHoldings");
    return saved ? JSON.parse(saved) : startingHoldings;
  });

  const [account, setAccount] = useState("");
  const [ticker, setTicker] = useState("");
  const [shares, setShares] = useState("");

  // Prices will be wired to a live market API next.
  // Until then, values show as "Pending".
  const prices = {};

  const groupedAccounts = useMemo(() => {
    return holdings.reduce((groups, holding) => {
      if (!groups[holding.account]) {
        groups[holding.account] = [];
      }

      groups[holding.account].push(holding);
      return groups;
    }, {});
  }, [holdings]);

  const accountSummaries = useMemo(() => {
    return Object.entries(groupedAccounts).map(([accountName, accountHoldings]) => {
      const knownValue = accountHoldings.reduce((sum, holding) => {
        const price = prices[holding.ticker];
        return price ? sum + holding.shares * price : sum;
      }, 0);

      const hasAllPrices = accountHoldings.every((holding) => prices[holding.ticker]);

      return {
        accountName,
        count: accountHoldings.length,
        knownValue,
        hasAllPrices,
      };
    });
  }, [groupedAccounts]);

  const portfolioValue = accountSummaries.reduce(
    (sum, accountSummary) => sum + accountSummary.knownValue,
    0
  );

  const hasFullPortfolioPricing = holdings.every((holding) => prices[holding.ticker]);

  const saveHoldings = (nextHoldings) => {
    setHoldings(nextHoldings);
    localStorage.setItem("portfolioHoldings", JSON.stringify(nextHoldings));
  };

  const addHolding = () => {
    if (!account.trim() || !ticker.trim() || !shares) return;

    const nextHoldings = [
      ...holdings,
      {
        account: account.trim(),
        ticker: ticker.trim().toUpperCase(),
        shares: Number(shares),
      },
    ];

    saveHoldings(nextHoldings);

    setAccount("");
    setTicker("");
    setShares("");
  };

  const deleteHolding = (indexToDelete) => {
    const nextHoldings = holdings.filter((_, index) => index !== indexToDelete);
    saveHoldings(nextHoldings);
  };

  const resetToStartingHoldings = () => {
    saveHoldings(startingHoldings);
  };

  const formatCurrency = (value, isComplete) => {
    if (!isComplete) return "Pricing pending";

    return value.toLocaleString(undefined, {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    });
  };

  return (
    <div className="space-y-5">
      <div className="bg-white p-6 rounded border">
        <h1 className="text-2xl font-bold mb-2">Finance</h1>
        <p className="text-sm text-slate-500">
          Portfolio holdings by account. Accounts are collapsed by default.
          Live pricing and daily change will be added next.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded border">
          <div className="text-xs uppercase text-slate-500">Portfolio Value</div>
          <div className="text-2xl font-bold mt-1">
            {formatCurrency(portfolioValue, hasFullPortfolioPricing)}
          </div>
        </div>

        <div className="bg-white p-5 rounded border">
          <div className="text-xs uppercase text-slate-500">Accounts</div>
          <div className="text-2xl font-bold mt-1">
            {Object.keys(groupedAccounts).length}
          </div>
        </div>

        <div className="bg-white p-5 rounded border">
          <div className="text-xs uppercase text-slate-500">Holdings</div>
          <div className="text-2xl font-bold mt-1">
            {holdings.length}
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded border">
        <h2 className="text-xl font-bold mb-4">Add Holding</h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            value={account}
            onChange={(e) => setAccount(e.target.value)}
            placeholder="Account"
            className="border rounded p-2"
          />

          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="Ticker"
            className="border rounded p-2"
          />

          <input
            value={shares}
            onChange={(e) => setShares(e.target.value)}
            placeholder="Shares"
            type="number"
            step="0.001"
            className="border rounded p-2"
          />

          <button
            onClick={addHolding}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            Add Holding
          </button>
        </div>

        <button
          onClick={resetToStartingHoldings}
          className="mt-3 bg-slate-200 text-slate-800 px-4 py-2 rounded text-sm"
        >
          Reset to Starting Holdings
        </button>
      </div>

      <div className="space-y-3">
        {Object.entries(groupedAccounts).map(([accountName, accountHoldings]) => {
          const summary = accountSummaries.find(
            (item) => item.accountName === accountName
          );

          return (
            <details key={accountName} className="bg-white rounded border" closed="true">
              <summary className="cursor-pointer p-5 list-none">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                  <div>
                    <div className="text-xl font-bold">{accountName}</div>
                    <div className="text-sm text-slate-500">
                      {accountHoldings.length} holdings
                    </div>
                  </div>

                  <div className="text-left md:text-right">
                    <div className="text-xs uppercase text-slate-500">
                      Account Value
                    </div>
                    <div className="text-lg font-bold">
                      {formatCurrency(summary?.knownValue || 0, summary?.hasAllPrices)}
                    </div>
                  </div>
                </div>
              </summary>

              <div className="px-5 pb-5">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="text-left p-2 border">Ticker</th>
                        <th className="text-right p-2 border">Shares</th>
                        <th className="text-right p-2 border">Price</th>
                        <th className="text-right p-2 border">Daily Change</th>
                        <th className="text-right p-2 border">Value</th>
                        <th className="text-left p-2 border">Action</th>
                      </tr>
                    </thead>

                    <tbody>
                      {accountHoldings.map((holding, localIndex) => {
                        const globalIndex = holdings.findIndex(
                          (item, index) =>
                            index >= 0 &&
                            item.account === holding.account &&
                            item.ticker === holding.ticker &&
                            item.shares === holding.shares
                        );

                        const price = prices[holding.ticker];
                        const value = price ? holding.shares * price : null;

                        return (
                          <tr key={`${holding.account}-${holding.ticker}-${localIndex}`}>
                            <td className="p-2 border font-semibold">{holding.ticker}</td>
                            <td className="p-2 border text-right">
                              {holding.shares.toLocaleString(undefined, {
                                maximumFractionDigits: 3,
                              })}
                            </td>
                            <td className="p-2 border text-right text-slate-400">
                              {price ? formatCurrency(price, true) : "Pending"}
                            </td>
                            <td className="p-2 border text-right text-slate-400">
                              Pending
                            </td>
                            <td className="p-2 border text-right text-slate-400">
                              {value ? formatCurrency(value, true) : "Pending"}
                            </td>
                            <td className="p-2 border">
                              <button
                                onClick={() => deleteHolding(globalIndex)}
                                className="text-red-600 hover:underline"
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
    </div>
  );
}

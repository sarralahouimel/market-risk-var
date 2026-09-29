import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm, chi2


TICKERS = ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL"]
WEIGHTS = np.array([0.25, 0.25, 0.20, 0.15, 0.15])
PORTFOLIO_VALUE = 100000
CONFIDENCE_LEVEL = 0.95
START_DATE = "2021-01-01"
END_DATE = "2026-01-01"


def download_data(tickers, start_date, end_date):
    data = yf.download(
        tickers,
        start=start_date,
        end=end_date,
        auto_adjust=True
    )

    prices = data["Close"].dropna()

    return prices


def calculate_returns(prices):
    returns = prices.pct_change().dropna()

    return returns

def calculate_portfolio_returns(returns, weights):
    portfolio_returns = returns.dot(weights)

    return portfolio_returns


def historical_var(portfolio_returns, confidence_level, portfolio_value):
    var_return = np.percentile(
        portfolio_returns,
        (1 - confidence_level) * 100
    )

    var_eur = abs(var_return * portfolio_value)

    return var_return, var_eur

def parametric_var(portfolio_returns, confidence_level, portfolio_value):
    mean_return = portfolio_returns.mean()
    std_return = portfolio_returns.std()

    z_score = norm.ppf(1 - confidence_level)

    var_return = mean_return + z_score * std_return
    var_eur = abs(var_return * portfolio_value)

    return var_return, var_eur

def monte_carlo_var(
    portfolio_returns,
    confidence_level,
    portfolio_value,
    n_simulations=10000,
    seed=42
):
    mean_return = portfolio_returns.mean()
    std_return = portfolio_returns.std()

    np.random.seed(seed)

    simulated_returns = np.random.normal(
        mean_return,
        std_return,
        n_simulations
    )

    var_return = np.percentile(
        simulated_returns,
        (1 - confidence_level) * 100
    )

    var_eur = abs(var_return * portfolio_value)

    return var_return, var_eur
def historical_cvar(
    portfolio_returns,
    var_return,
    portfolio_value
):
    tail_losses = portfolio_returns[
        portfolio_returns <= var_return
    ]

    cvar_return = tail_losses.mean()
    cvar_eur = abs(cvar_return * portfolio_value)

    return cvar_return, cvar_eur

def backtest_var(
    portfolio_returns,
    var_eur,
    portfolio_value
):
    portfolio_pnl = portfolio_returns * portfolio_value

    var_threshold = -var_eur

    exceptions = portfolio_pnl[
        portfolio_pnl < var_threshold
    ]

    exception_rate = len(exceptions) / len(portfolio_pnl)

    return portfolio_pnl, exceptions, exception_rate 

def kupiec_test(
    n_observations,
    n_exceptions,
    confidence_level
):
    expected_exception_rate = 1 - confidence_level
    observed_exception_rate = n_exceptions / n_observations

    lr_uc = -2 * (
        (n_observations - n_exceptions)
        * np.log(
            (1 - expected_exception_rate)
            / (1 - observed_exception_rate)
        )
        + n_exceptions
        * np.log(
            expected_exception_rate
            / observed_exception_rate
        )
    )

    p_value = 1 - chi2.cdf(lr_uc, df=1)

    return lr_uc, p_value
if __name__ == "__main__":
    prices = download_data(
        TICKERS,
        START_DATE,
        END_DATE
    )

    returns = calculate_returns(prices)

    portfolio_returns = calculate_portfolio_returns(
        returns,
        WEIGHTS
    )

    var_return, var_eur = historical_var(
        portfolio_returns,
        CONFIDENCE_LEVEL,
        PORTFOLIO_VALUE
    )

    param_var_return, param_var_eur = parametric_var(
        portfolio_returns,
        CONFIDENCE_LEVEL,
        PORTFOLIO_VALUE
    )

    mc_var_return, mc_var_eur = monte_carlo_var(
    portfolio_returns,
    CONFIDENCE_LEVEL,
    PORTFOLIO_VALUE
    )
    cvar_return, cvar_eur = historical_cvar(
    portfolio_returns,
    var_return,
    PORTFOLIO_VALUE
)

    portfolio_pnl, exceptions, exception_rate = backtest_var(
    portfolio_returns,
    var_eur,
    PORTFOLIO_VALUE
)
    lr_uc, p_value = kupiec_test(
    len(portfolio_pnl),
    len(exceptions),
    CONFIDENCE_LEVEL
)
print("\n" + "=" * 50)
print("MARKET RISK ANALYSIS - VALUE AT RISK")
print("=" * 50)

print(f"Portfolio value: {PORTFOLIO_VALUE:,.2f} €")
print(f"Confidence level: {CONFIDENCE_LEVEL:.0%}")
print(f"Period: {START_DATE} to {END_DATE}")

print("\n--- Risk Metrics ---")
print(f"Historical VaR 95%: {var_eur:,.2f} €")
print(f"Parametric VaR 95%: {param_var_eur:,.2f} €")
print(f"Monte Carlo VaR 95%: {mc_var_eur:,.2f} €")
print(f"Historical CVaR 95%: {cvar_eur:,.2f} €")

print("\n--- Backtesting ---")
print(f"Backtesting days: {len(portfolio_pnl)}")
print(f"VaR exceptions: {len(exceptions)}")
print(f"Exception rate: {exception_rate:.2%}")

print("\n--- Kupiec Test ---")
print(f"LR statistic: {lr_uc:.4f}")
print(f"P-value: {p_value:.4f}")

print("=" * 50)

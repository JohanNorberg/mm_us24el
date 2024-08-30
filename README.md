# Manifold Market US 2024 Election Forecast

https://manifold.markets/

Polls state markets created by https://manifold.markets/ManifoldPolitics for the 2024 US Presidential Election, and runs simulations to forecast the outcome.

## Current EV Distribution

Shows the current distribution of Electoral Votes (EV) giving the party with >50% the win.

## Monte Carlo Simulation

Runs 100,000 simulations of the election, and shows the percentage won and distribution of EVs for each party.

## Adjusted Monte Carlo Simulation

Same as Monte Carlo except it moves <25% to 0% and >75% to 100%. For example this gives Texas (https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-2ad2e0596c59) 100% to Republicans.

## Adjusted with Correlations Monte Carlo Simulation

Uses https://manifold.markets/EvanDaniel/pairwise-state-results-which-pairs to adjust the Monte Carlo simulation based on correlations between states.

Adjusted odds

```
def adjust_odds(x):

    if x < 0.25:
        return 0
    elif x > 0.75:
        return 1
    else:
        return x
```

## Reference

Github: https://github.com/JohanNorberg/mm_us24el
Website: https://johannorberg.github.io/mm_us24el/
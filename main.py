import random
from datetime import datetime

import diskcache as dc
import markdown
import requests
from jinja2 import Environment, FileSystemLoader

# Initialize a cache with a specific directory
cache = dc.Cache('./cache')

markets = []
state_pairs = []

simulations=500_000

state_map = {
        'AL': 'Alabama',
        'AK': 'Alaska',
        'AZ': 'Arizona',
        'AR': 'Arkansas',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DE': 'Delaware',
        'DC': 'District of Columbia',
        'FL': 'Florida',
        'GA': 'Georgia',
        'HI': 'Hawaii',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'IA': 'Iowa',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'ME': 'Maine-State',
        'ME-1': 'Maine-ME-1',
        'ME-2': 'Maine-ME-2',
        'MD': 'Maryland',
        'MA': 'Massachusetts',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MS': 'Mississippi',
        'MO': 'Missouri',
        'MT': 'Montana',
        'NE': 'Nebraska-State',
        'NE-1': 'Nebraska-NE-1',
        'NE-2': 'Nebraska-NE-2',
        'NE-3': 'Nebraska-NE-3',
        'NV': 'Nevada',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NY': 'New York',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VT': 'Vermont',
        'VA': 'Virginia',
        'WA': 'Washington',
        'WV': 'West Virginia',
        'WI': 'Wisconsin',
        'WY': 'Wyoming'
    }

inverse_state_map = {v: k for k, v in state_map.items()}



def get_state_long_name(short_name):

    if short_name not in state_map:
        raise KeyError(f"State abbreviation '{short_name}' not found.")

    return state_map[short_name]

def get_state_short_name(long_name):

    if long_name not in inverse_state_map:
        raise KeyError(f"State '{long_name}' not found.")

    return inverse_state_map[long_name]

swing_states = ['Wisconsin', 'Michigan', 'Nevada', 'Pennsylvania', 'North Carolina', 'Georgia', 'Arizona']
swing_states_short = [get_state_short_name(state) for state in swing_states]

def adjust_odds(x):

    if x < 0.25:
        return 0
    elif x > 0.75:
        return 1
    else:
        return x

    #amount = 0.1
    #return max(0, min(1, ((x - 0.5) / (1.0 - amount)) + 0.5))

def get_initial_votes():
    """Calculate initial vote counts based on probabilities."""
    democrat_votes = 0
    republican_votes = 0
    democrat_states = []
    republican_states = []

    for market in markets:
        if market['democrat_probability'] > market['republican_probability']:
            democrat_votes += market['votes']
            democrat_states.append(market['name'])
        else:
            republican_votes += market['votes']
            republican_states.append(market['name'])

    return democrat_votes, republican_votes, democrat_states, republican_states

def simulate_elections():
    """Simulate elections multiple times and collect results."""
    results = []

    for _ in range(simulations):
        democrat_votes_sim = 0
        republican_votes_sim = 0
        democrat_states_sim = []
        republican_states_sim = []

        for market in markets:
            if random.random() < market['democrat_probability']:
                democrat_votes_sim += market['votes']
                democrat_states_sim.append(market['name'])
            else:
                republican_votes_sim += market['votes']
                republican_states_sim.append(market['name'])

        results.append({
            'democrat_votes_simulation': democrat_votes_sim,
            'republican_votes_simulation': republican_votes_sim,
            'democrat_states_simulation': democrat_states_sim,
            'republican_states_simulation': republican_states_sim
        })

    return results


def simulate_elections_with_pairs():
    """Simulate elections multiple times with state pairs considered."""
    results = []

    for _ in range(simulations):
        democrat_votes_sim = 0
        republican_votes_sim = 0
        democrat_states_sim = []
        republican_states_sim = []

        # Keep track of the states that have already been decided
        decided_states = set()

        # Shuffle state pairs for randomness
        random.shuffle(state_pairs)

        states_d_win = {}


        for pair in state_pairs:
            state1 = get_state_long_name(pair['states1'])
            state2 = get_state_long_name(pair['states2'])
            probability_same = adjust_odds(pair['probability']) # the probability they are the same


            if random.random() < 0.5:
                tmp = state1
                state1 = state2
                state2 = tmp

            if state1 in decided_states and state2 in decided_states:
                continue # Skip if both states have already been decided

            if state1 in decided_states:
                if random.random() < probability_same:
                    states_d_win[state2] = states_d_win[state1]
                else:
                    states_d_win[state2] = not states_d_win[state1]

                decided_states.add(state2)
                continue

            if state2 in decided_states:
                if random.random() < probability_same:
                    states_d_win[state1] = states_d_win[state2]
                else:
                    states_d_win[state1] = not states_d_win[state2]

                decided_states.add(state1)
                continue

            # Neither has been decided. Check if state1 is democrat win, and then decide state2 based on probability_same

            state1_market_democrat_probability = adjust_odds(markets[[market['name'] for market in markets].index(state1)]['democrat_probability'])

            if random.random() < state1_market_democrat_probability:
                states_d_win[state1] = True
            else:
                states_d_win[state1] = False

            if random.random() < probability_same:
                states_d_win[state2] = states_d_win[state1]
            else:
                states_d_win[state2] = not states_d_win[state1]

            decided_states.add(state1)
            decided_states.add(state2)

        for state in states_d_win:
            if states_d_win[state]:
                democrat_votes_sim += markets[[market['name'] for market in markets].index(state)]['votes']
                democrat_states_sim.append(state)
            else:
                republican_votes_sim += markets[[market['name'] for market in markets].index(state)]['votes']
                republican_states_sim.append(state)

        # Then add the remaining states

        for market in markets:
            if market['name'] not in decided_states:
                if random.random() < adjust_odds(market['democrat_probability']):
                    democrat_votes_sim += market['votes']
                    democrat_states_sim.append(market['name'])
                else:
                    republican_votes_sim += market['votes']
                    republican_states_sim.append(market['name'])

        results.append({
            'democrat_votes_simulation': democrat_votes_sim,
            'republican_votes_simulation': republican_votes_sim,
            'democrat_states_simulation': democrat_states_sim,
            'republican_states_simulation': republican_states_sim
        })

    return results


def simulate_elections_adjusted():
    results = []

    for _ in range(simulations):
        democrat_votes_sim = 0
        republican_votes_sim = 0
        democrat_states_sim = []
        republican_states_sim = []

        for market in markets:

            # Adjust probabilities so anything below 0.25 is 0 and above 0.75 is 1
            democrat_probability = market['democrat_probability']

            if democrat_probability < 0.25:
                democrat_probability = 0
            elif democrat_probability > 0.75:
                democrat_probability = 1

            if random.random() < democrat_probability:
                democrat_votes_sim += market['votes']
                democrat_states_sim.append(market['name'])
            else:
                republican_votes_sim += market['votes']
                republican_states_sim.append(market['name'])

        results.append({
            'democrat_votes_simulation': democrat_votes_sim,
            'republican_votes_simulation': republican_votes_sim,
            'democrat_states_simulation': democrat_states_sim,
            'republican_states_simulation': republican_states_sim
        })

    return results

def simulate_elections_only_swing_states(): 
    # If it's a swing state, use the odds without adjustment
    # If it's not a swing state, set odds to 0 or 1 based on the closest probability

    results = []

    for idx in range(simulations):
        democrat_votes_sim = 0
        republican_votes_sim = 0
        democrat_states_sim = []
        republican_states_sim = []

        for market in markets:

            democrat_probability = market['democrat_probability']

            if market['name'] not in swing_states:
                if democrat_probability < 0.5:
                    democrat_probability = 0
                else:
                    democrat_probability = 1
            else:
                if idx == 0:
                    print(market['name'], democrat_probability)
            
            if random.random() < democrat_probability:
                democrat_votes_sim += market['votes']

                if market['name'] in swing_states:
                    democrat_states_sim.append(market['name'])
            else:
                republican_votes_sim += market['votes']

                if market['name'] in swing_states:
                    republican_states_sim.append(market['name'])

        results.append({
            'democrat_votes_simulation': democrat_votes_sim,
            'republican_votes_simulation': republican_votes_sim,
            'democrat_states_simulation': democrat_states_sim,
            'republican_states_simulation': republican_states_sim
        })

    return results




def calculate_probabilities(results):
    """Calculate the number of wins and probabilities."""
    democrat_wins = sum(
        1 for result in results if result['democrat_votes_simulation'] > result['republican_votes_simulation'])
    republican_wins = simulations - democrat_wins

    return democrat_wins, republican_wins, democrat_wins / simulations, republican_wins / simulations

def get_median_results(results):
    """Get the median votes and states from simulations."""
    results_sorted = sorted(results, key=lambda x: x['democrat_votes_simulation'])
    median_result = results_sorted[len(results_sorted) // 2]
    return median_result

def calculate_odds():


    # Step 1: Calculate initial votes based on probabilities
    democrat_votes, republican_votes, democrat_states, republican_states = get_initial_votes()
    simulation_results = simulate_elections()

    # Step 3: Calculate probabilities and median results
    democrat_wins, republican_wins, democrat_prob, republican_prob = calculate_probabilities(simulation_results)
    median_result = get_median_results(simulation_results)

    # Step 4: Simulate elections with adjusted probabilities
    simulation_results_adjusted = simulate_elections_adjusted()

    # Step 5: Calculate probabilities and median results for adjusted probabilities
    democrat_wins_adjusted, republican_wins_adjusted, democrat_prob_adjusted, republican_prob_adjusted = calculate_probabilities(
        simulation_results_adjusted)
    median_result_adjusted = get_median_results(simulation_results_adjusted)

    simulation_results_with_pairs = simulate_elections_with_pairs()

    democrat_wins_with_pairs, republican_wins_with_pairs, democrat_prob_with_pairs, republican_prob_with_pairs = calculate_probabilities(
        simulation_results_with_pairs)
    median_result_with_pairs = get_median_results(simulation_results_with_pairs)

    #print(democrat_wins_with_pairs, republican_wins_with_pairs, democrat_prob_with_pairs, republican_prob_with_pairs)

    # Step 6: Simulate elections with only swing states
    simulation_results_only_swing_states = simulate_elections_only_swing_states()

    # Step 7: Calculate probabilities and median results for only swing states
    democrat_wins_only_swing_states, republican_wins_only_swing_states, democrat_prob_only_swing_states, republican_prob_only_swing_states = calculate_probabilities(
        simulation_results_only_swing_states)
    median_result_only_swing_states = get_median_results(simulation_results_only_swing_states)


    return {
        'simple': {
            'democrat_votes': democrat_votes,
            'republican_votes': republican_votes,
            'democrat_states': democrat_states,
            'republican_states': republican_states
        },
        'simulation': {
            'democrat_wins': democrat_wins,
            'republican_wins': republican_wins,
            'democrat_votes_median': median_result['democrat_votes_simulation'],
            'republican_votes_median': median_result['republican_votes_simulation'],
            'democrat_states_median': median_result['democrat_states_simulation'],
            'republican_states_median': median_result['republican_states_simulation'],
            'democrat_probability': democrat_prob,
            'republican_probability': republican_prob
        },
        'simulation_adjusted': {
            'democrat_wins': democrat_wins_adjusted,
            'republican_wins': republican_wins_adjusted,
            'democrat_votes_median': median_result_adjusted['democrat_votes_simulation'],
            'republican_votes_median': median_result_adjusted['republican_votes_simulation'],
            'democrat_states_median': median_result_adjusted['democrat_states_simulation'],
            'republican_states_median': median_result_adjusted['republican_states_simulation'],
            'democrat_probability': democrat_prob_adjusted,
            'republican_probability': republican_prob_adjusted
        },
        'simulation_with_pairs': {
            'democrat_wins': democrat_wins_with_pairs,
            'republican_wins': republican_wins_with_pairs,
            'democrat_votes_median': median_result_with_pairs['democrat_votes_simulation'],
            'republican_votes_median': median_result_with_pairs['republican_votes_simulation'],
            'democrat_states_median': median_result_with_pairs['democrat_states_simulation'],
            'republican_states_median': median_result_with_pairs['republican_states_simulation'],
            'democrat_probability': democrat_prob_with_pairs,
            'republican_probability': republican_prob_with_pairs
        },
        'simulation_only_swing_states': {
            'democrat_wins': democrat_wins_only_swing_states,
            'republican_wins': republican_wins_only_swing_states,
            'democrat_votes_median': median_result_only_swing_states['democrat_votes_simulation'],
            'republican_votes_median': median_result_only_swing_states['republican_votes_simulation'],
            'democrat_states_median': median_result_only_swing_states['democrat_states_simulation'],
            'republican_states_median': median_result_only_swing_states['republican_states_simulation'],
            'democrat_probability': democrat_prob_only_swing_states,
            'republican_probability': republican_prob_only_swing_states
        }
    }


@cache.memoize(expire=1800)
def get_correlation_odds():
    url = 'https://manifold.markets/EvanDaniel/pairwise-state-results-which-pairs'
    slug = url.split('/')[-1]
    url = f'https://api.manifold.markets/v0/slug/{slug}'
    r = requests.get(url)

    if r.status_code != 200:
        print('Error getting correlation odds', r.status_code)
        raise Exception('Error getting correlation odds')

    correlation_odds = r.json()

    print('correlation', correlation_odds)

    return correlation_odds



def register_correlations():
    correlation_odds = get_correlation_odds()

    for pair in correlation_odds['answers']:
        text = pair['text']

        states = text.split(' and ')
        state1 = states[0]
        state2 = states[1]

        state_pairs.append({
            'states1': state1,
            'states2': state2,
            'probability': pair['probability']
        })

@cache.memoize(expire=1800)
def get_market_odds(name, votes, manifold_markets_url):
    print('get market', name, votes, manifold_markets_url)

    # get slug by getting string after last /
    slug_name = manifold_markets_url.split('/')[-1]

    url = f'https://api.manifold.markets/v0/slug/{slug_name}'
    r = requests.get(url)

    if r.status_code != 200:
        print('Error getting market', r.status_code)
        raise Exception('Error getting market')

    market = r.json()

    print('market', market)

    # Find answer that text to lower contains 'democrat' if it's not exactly one raise exception
    democrat_answer = None
    republican_answer = None
    for answer in market['answers']:
        if 'democrat' in answer['text'].lower():
            if democrat_answer:
                raise Exception('More than one democrat answer')
            democrat_answer = answer
        if 'republican' in answer['text'].lower():
            if republican_answer:
                raise Exception('More than one republican answer')
            republican_answer = answer

    if not democrat_answer:
        raise Exception('No democrat answer')
    if not republican_answer:
        raise Exception('No republican answer')

    democrat_probability = democrat_answer['probability']
    republican_probability = republican_answer['probability']

    # Normalize probabilities so sum is 1
    total_probability = democrat_probability + republican_probability
    democrat_probability /= total_probability
    republican_probability /= total_probability

    print('democrat_probability', democrat_probability)
    print('republican_probability', republican_probability)

    return {
        'name': name,
        'votes': votes,
        'democrat_probability': democrat_probability,
        'republican_probability': republican_probability,
        'link': manifold_markets_url
    }


def register_market(name, votes, manifold_markets_url):
    market = get_market_odds(name, votes, manifold_markets_url)
    markets.append(market)


def register_markets():


    register_market('Alabama', 9,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-98654274ab42')
    register_market('Alaska', 3,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-3834d8e5168f')
    register_market('Arizona', 11,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-c1307cf9f69a')
    register_market('Arkansas', 6,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-e845a612e2a4')
    register_market('California', 54,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-26a1eb1b8ce6')
    register_market('Colorado', 10,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-995251995021')
    register_market('Connecticut', 7,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-12e8e8ae4aee')
    register_market('Delaware', 3,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-86216dcc6ec8')
    register_market('District of Columbia', 3,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-11704714dec4')
    register_market('Florida', 30,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-a0c0e217efb2')
    register_market('Georgia', 16,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-9d5b554982a7')
    register_market('Hawaii', 4,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-878851234156')
    register_market('Idaho', 4,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-e762820f4b34')
    register_market('Illinois', 19,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-c506aa98d74d')
    register_market('Indiana', 11,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-5414030a4a48')
    register_market('Iowa', 6,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-31c9af68dec9')
    register_market('Kansas', 6,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-4df471a7f5e3')
    register_market('Kentucky', 8,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-52290675de33')
    register_market('Louisiana', 8,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-7047ba212e02')
    register_market('Maine-State', 2,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-af574b601b0f')
    register_market('Maine-ME-1', 1,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-a17ba873a3c1')
    register_market('Maine-ME-2', 1,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-5163ceb2f4a9')
    register_market('Maryland', 10,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-e43222661719')
    register_market('Massachusetts', 11,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-dcff5d64dbc8')
    register_market('Michigan', 15,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-7e7362326c95')
    register_market('Minnesota', 10,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-052a52f54c0e')
    register_market('Mississippi', 6,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-859f4dab533d')
    register_market('Missouri', 10,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-1ccd026993f1')
    register_market('Montana', 4,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-5406455b109d')
    register_market('Nebraska-State', 2,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-3c332029e300')
    register_market('Nebraska-NE-1', 1,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-cf2823625bd9')
    register_market('Nebraska-NE-2', 1,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-389edd65ace9')
    register_market('Nebraska-NE-3', 1,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-73dbbe3d114f')
    register_market('Nevada', 6,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-5777ea10ce2a')
    register_market('New Hampshire', 4,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-458f2140827c')
    register_market('New Jersey', 14,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-96f0176fbd5a')
    register_market('New Mexico', 5,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-c98c13402468')
    register_market('New York', 28,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-7c957d5b5e4c')
    register_market('North Carolina', 16,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-c2b132de8821')
    register_market('North Dakota', 3,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-fab2b645d9d3')
    register_market('Ohio', 17,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-f2f89eddc252')
    register_market('Oklahoma', 7,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-8144295e678c')
    register_market('Oregon', 8,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-c24796f7ea73')
    register_market('Pennsylvania', 19, 'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside')
    register_market('Rhode Island', 4,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-f7998626f959')
    register_market('South Carolina', 9,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-f0e933a475d1')
    register_market('South Dakota', 3,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-bc361a1e7ca0')
    register_market('Tennessee', 11,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-a870c481a5ce')
    register_market('Texas', 40,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-2ad2e0596c59')
    register_market('Utah', 6,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-9cd88c5b9389')
    register_market('Vermont', 3,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-7b9db14c6562')
    register_market('Virginia', 13,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-6db80c968e21')
    register_market('Washington', 12,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-8b4af904766d')
    register_market('West Virginia', 4,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-3ffb4d1203a0')
    register_market('Wisconsin', 10,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-ee07598f45ea')
    register_market('Wyoming', 3,
                    'https://manifold.markets/ManifoldPolitics/which-party-will-win-the-us-preside-686f75d3998e')


def a_to_s(state_names):
    return ', '.join(state_names[:-1]) + ' and ' + state_names[-1]

if __name__ == '__main__':
    register_markets()
    register_correlations()
    odds_data = calculate_odds()

    # Load the Jinja2 template from the file
    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template('jinja_template.txt')

    total_ev = 538

    mapped_states = [
        {
            'name': state['name'],
            'ev': state['votes'],
            'democrat_percent': round(state['democrat_probability'] * 100, 1),
            'republican_percent': round(state['republican_probability'] * 100, 1),
            'link': state['link']
        }
        for state in markets
    ]

    mapped_odds_data = {
        'simple': {
            'democrat_votes': odds_data['simple']['democrat_votes'],
            'republican_votes': odds_data['simple']['republican_votes'],
            'democrat_percentage': round((odds_data['simple']['democrat_votes'] / total_ev) * 100),
            'republican_percentage': round((odds_data['simple']['republican_votes'] / total_ev) * 100),
            'democrat_states': a_to_s(list(map(get_state_short_name, odds_data['simple']['democrat_states']))),
            'republican_states': a_to_s(list(map(get_state_short_name, odds_data['simple']['republican_states'])))
        },
        'simulation': {
            'democrat_wins': odds_data['simulation']['democrat_wins'],
            'republican_wins': odds_data['simulation']['republican_wins'],
            'democrat_votes_median': odds_data['simulation']['democrat_votes_median'],
            'republican_votes_median': odds_data['simulation']['republican_votes_median'],
            'democrat_votes_median_percent': round((odds_data['simulation']['democrat_votes_median'] / total_ev) * 100),
            'republican_votes_median_percent': round(
                (odds_data['simulation']['republican_votes_median'] / total_ev) * 100),
            'democrat_states': a_to_s(list(map(get_state_short_name, odds_data['simulation']['democrat_states_median']))),
            'republican_states': a_to_s(list(map(get_state_short_name, odds_data['simulation']['republican_states_median']))),
            'democrat_probability': round(odds_data['simulation']['democrat_probability'] * 100),
            'republican_probability': round(odds_data['simulation']['republican_probability'] * 100)
        },
        'simulation_adjusted': {
            'democrat_wins': odds_data['simulation_adjusted']['democrat_wins'],
            'republican_wins': odds_data['simulation_adjusted']['republican_wins'],
            'democrat_votes_median': odds_data['simulation_adjusted']['democrat_votes_median'],
            'republican_votes_median': odds_data['simulation_adjusted']['republican_votes_median'],
            'democrat_votes_median_percent': round(
                (odds_data['simulation_adjusted']['democrat_votes_median'] / total_ev) * 100),
            'republican_votes_median_percent': round(
                (odds_data['simulation_adjusted']['republican_votes_median'] / total_ev) * 100),
            'democrat_states': a_to_s(list(map(get_state_short_name, odds_data['simulation_adjusted']['democrat_states_median']))),
            'republican_states': a_to_s(list(map(get_state_short_name, odds_data['simulation_adjusted']['republican_states_median']))),
            'democrat_probability': round(odds_data['simulation_adjusted']['democrat_probability'] * 100),
            'republican_probability': round(odds_data['simulation_adjusted']['republican_probability'] * 100)
        },
        'simulation_with_pairs': {
            'democrat_wins': odds_data['simulation_with_pairs']['democrat_wins'],
            'republican_wins': odds_data['simulation_with_pairs']['republican_wins'],
            'democrat_votes_median': odds_data['simulation_with_pairs']['democrat_votes_median'],
            'republican_votes_median': odds_data['simulation_with_pairs']['republican_votes_median'],
            'democrat_votes_median_percent': round(
                (odds_data['simulation_with_pairs']['democrat_votes_median'] / total_ev) * 100),
            'republican_votes_median_percent': round(
                (odds_data['simulation_with_pairs']['republican_votes_median'] / total_ev) * 100),
            'democrat_states': a_to_s(list(map(get_state_short_name, odds_data['simulation_with_pairs']['democrat_states_median']))),
            'republican_states': a_to_s(list(map(get_state_short_name, odds_data['simulation_with_pairs']['republican_states_median']))),
            'democrat_probability': round(odds_data['simulation_with_pairs']['democrat_probability'] * 100),
            'republican_probability': round(odds_data['simulation_with_pairs']['republican_probability'] * 100)
        },
        'simulation_only_swing_states': {
            'democrat_wins': odds_data['simulation_only_swing_states']['democrat_wins'],
            'republican_wins': odds_data['simulation_only_swing_states']['republican_wins'],
            'democrat_votes_median': odds_data['simulation_only_swing_states']['democrat_votes_median'],
            'republican_votes_median': odds_data['simulation_only_swing_states']['republican_votes_median'],
            'democrat_votes_median_percent': round(
                (odds_data['simulation_only_swing_states']['democrat_votes_median'] / total_ev) * 100),
            'republican_votes_median_percent': round(
                (odds_data['simulation_only_swing_states']['republican_votes_median'] / total_ev) * 100),
            'democrat_states': a_to_s(list(map(get_state_short_name, odds_data['simulation_only_swing_states']['democrat_states_median']))),
            'republican_states': a_to_s(list(map(get_state_short_name, odds_data['simulation_only_swing_states']['republican_states_median']))),
            'democrat_probability': round(odds_data['simulation_only_swing_states']['democrat_probability'] * 100),
            'republican_probability': round(odds_data['simulation_only_swing_states']['republican_probability'] * 100)
        }    
    }

    # Get the current UTC time and format it as a readable string
    current_time_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    with open("README.md", "r") as f:
        readme = f.read()

    readme_html = markdown.markdown(readme)

    rendered_html = template.render(simple=mapped_odds_data['simple'],
                                    simulation=mapped_odds_data['simulation'],
                                    simulation_adjusted=mapped_odds_data['simulation_adjusted'],
                                    simulation_with_pairs=mapped_odds_data['simulation_with_pairs'],
                                    simulation_only_swing_states=mapped_odds_data['simulation_only_swing_states'],
                                    states=mapped_states,
                                    total_ev=total_ev,
                                    timestamp=current_time_utc,
                                    readme_html=readme_html)

    # Save the rendered HTML to a file
    with open('index.html', 'w') as f:
        f.write(rendered_html)

    print("HTML site generated and saved as 'index.html'")

from nltk.corpus import names
import pandas as pd
import random

class Analyst:

    def __init__(self, name, clas, perf, prefs):
        '''
        clas: (int) the class of the analyst
        perf: (int) the performance rating of the analyst
        prefs: ()
        '''
        assert isinstance(clas, int), "Pass 'clas' as an integer."
        assert isinstance(perf, int), "Pass 'perf' as an integer."
        assert isinstance(prefs, dict), "Pass preferences as a dictionary."

        self.name = name
        self.clas = clas
        self.perf = perf
        self.prefs = prefs
        self.inv_prefs = {v:k for k, v in self.prefs.items()}
        self.prefs_exhausted = 0

    def __repr__(self):
        return self.name

class Team:

    def __init__(self, name, headcount, ratings=None):
        '''
        headcount: (int) the headcount of the team
        ratings: (dict) a dictionary mapping teams
        '''
        self.name = name
        self.headcount = headcount
        self.ratings = ratings

    def __repr__(self):
        return self.name

class Schema:

    def __init__(self, analysts, teams):
        for analyst in analysts:
            if not isinstance(analyst, Analyst):
                raise ValueError('Not an analyst.')
        for team in teams:
            if not isinstance(team, Team):
                raise ValueError('Not a team.')

        self.analysts = analysts
        self.teams = teams
        self.n_analysts = len(analysts)
        self.n_teams = len(teams)
        self.total_hc = 0
        for team in self.teams:
            self.total_hc += team.headcount
        self.placements = None
        self.random_tbs = 0
        self.random_tbs_data = []
        self.log = {}
        self.log_txt = ''

    def __repr__(self):
        template = 'Schema with {} analysts, {} teams, and {} headcount'
        message = template.format(self.n_teams, self.n_teams, self.total_hc)
        return message

    def json(self):
        meta = {'Analysts':{}, 'Teams': {}}
        for team in self.teams:
            team_dict = {'Headcount': team.headcount,
                         'Ratings': team.ratings
                         }
            meta['Teams'][team.name] = team_dict

        for analyst in self.analysts:
            analyst_dict = {'Class': analyst.clas,
                            'Performance': analyst.perf,
                            'Preferences': analyst.prefs
                            }
            meta['Analysts'][analyst.name] = analyst_dict
        return meta

    def random_tiebreak(self, analyst_a, analyst_b, team, rank_type):
        '''Randomly break a tie between two analysts and record the results.
        '''
        shuffle = random.sample([analyst_a, analyst_b], 2)
        winner, loser = shuffle[0], shuffle[1]
        self.random_tbs += 1
        report = {'Winner': winner, 'Loser': loser,
                  'Team': team, 'Rank Type': rank_type}
        self.random_tbs_data.append(report)
        return winner

    def record(self, text, noisy=True):
        '''
        Function for logging algorithm behavior in text.
        (This is now logged in JSON, but we keep the text logging for fun,
        expanatory notation such as "At last! Convergence."
        '''
        if noisy:
            print(text)
        self.log_txt += '\n'
        self.log_txt += str(text)

    def precedence(self, analyst_a, analyst_b, team, rank_type):
        '''Given two analysts, a team, and a "rank_type", determine which analyst
        should receive precedence over the other on that team.
        analyst_a: (Analyst)
        analyst_b: (Analyst)
        '''
        assert isinstance(analyst_a, Analyst)
        assert isinstance(analyst_b, Analyst)
        assert isinstance(team, Team)
        accepted_rank_types = ['fulltime', 'rotation']
        assert rank_type in accepted_rank_types

        a_class, b_class = analyst_a.clas, analyst_b.clas
        a_perf, b_perf = analyst_a.perf, analyst_b.perf
        a_pref, b_pref = analyst_a.prefs[team.name], analyst_b.prefs[team.name]
        if rank_type == 'fulltime':
            a_rating, b_rating = team.ratings[analyst_a.name], team.ratings[analyst_b.name]

        if rank_type == 'fulltime':
            if a_rating < b_rating:
                return analyst_a
            elif b_rating < a_rating:
                return analyst_b
            #Now that rating is discrete, this never happens:
            else:
                if a_pref > b_pref:
                    return analyst_a
                elif b_pref > a_pref:
                    return analyst_b
                else:
                    if a_perf > b_perf:
                        return analyst_a
                    elif b_perf > a_perf:
                        return analyst_b
                    else:
                        return self.random_tiebreak(analyst_a, analyst_b,
                                                    team, rank_type)
        elif rank_type == 'rotation':
            if a_pref < b_pref:
                return analyst_a
            elif b_pref < a_pref:
                return analyst_b
            else:
                if a_class < b_class:
                    return analyst_a
                elif b_class < a_class:
                    return analyst_b
                else:
                    if a_perf > b_perf:
                        return analyst_a
                    elif b_perf > a_perf:
                        return analyst_b
                    else:
                        return self.random_tiebreak(analyst_a, analyst_b,
                                                    team, rank_type)

    def sort_analysts(self, analysts, team, ranktype):
        '''
        Sorts the analysts based on the precedence hierarchy.
        (Selection sort.)
        '''
        sorted_analysts = []
        unsorted_analysts = analysts
        for i in range(len(analysts)):
            top_analyst = unsorted_analysts[0]
            for analyst in unsorted_analysts[1:]:
                if self.precedence(analyst, top_analyst, team, ranktype) == analyst:
                    top_analyst = analyst
            sorted_analysts.append(unsorted_analysts.pop(unsorted_analysts.index(top_analyst)))
        return sorted_analysts

    def set_placements(self, ranktype, noisy=True):
        '''
        For now, only doing inter-rotational placements!

        fulltime_class: (int) Denotes the senior-most class that the algorithm
            should consider for full-time, rather than inter-rotational,
            placement. CURRENTLY NOT IN USE.

        noisy: (bool) Set to True for messaging about the algorithm's
            iterations, or False if you want it to run quietly, with no
            messages.
        '''

        placements = {team.name: [] for team in self.teams}
        if ranktype == 'fulltime':
            #TODO: Clean this up some day.
            #Need to do some very hacky stuff to re-order optimization criteria.
            for analyst in self.analysts:
                new_inv_prefs = {} #Overriding the hierarchy
                teams_ratings = [] #What the teams ranked them. (team, their_rank, your_rank)
                for team in self.teams:
                    for rated_analyst, rating in team.ratings.items():
                        if rated_analyst == analyst.name:
                            try:
                                analyst_pref = analyst.prefs[team.name]
                            except KeyError:
                                msg = f'Cannot find {analyst.name} preference for {team.name}'
                                raise Exception(msg)
                            teams_ratings.append((team.name, rating, analyst_pref))
                #Sorting. Very ugly. Not readable.
                sorted_teams_ratings = sorted(teams_ratings, key=lambda row: (row[1], row[2]))
                new_inv_prefs = {i: team_tuple[0] for i, team_tuple in enumerate(sorted_teams_ratings, 0)}
                print('heres that thing')
                print(new_inv_prefs)
                analyst.inv_prefs = new_inv_prefs

        for analyst in self.analysts:
            top_team = analyst.inv_prefs[0]
            placements[top_team].append(analyst)

        converged = False
        i = 1
        while not converged:
            unassigned_analysts = []
            iteration = 'Iteration {}'.format(i)
            self.log[iteration] = {}
            self.record('#### Iteration {} ####'.format(i), noisy)
            self.record('Starting Placements:', noisy)
            self.record(placements, noisy)
            self.log[iteration]['Starting Placements'] = placements
            for team in self.teams:
                tn = team.name
                if len(placements[tn]) > team.headcount:
                    sorted_analysts = self.sort_analysts(placements[tn],
                                                         team, ranktype)
                    staying_analysts = sorted_analysts[:team.headcount]
                    leaving_analysts = sorted_analysts[team.headcount:]
                    placements[tn] = staying_analysts
                    unassigned_analysts += leaving_analysts
            self.record('Sorted Placements:', noisy)
            self.record(placements, noisy)
            self.log[iteration]['Sorted Placements'] = placements

            for analyst in unassigned_analysts:
                analyst.prefs_exhausted += 1
                try:
                    next_team = analyst.inv_prefs[analyst.prefs_exhausted]
                except:
                    msg = f'We are unable to place {analyst.name} on a team.'
                    raise Exception(msg)
                placements[next_team].append(analyst)

            if unassigned_analysts:
                n_unassigned = str(len(unassigned_analysts))
                self.record('{} still unassigned:'.format(n_unassigned), noisy)
                self.record(unassigned_analysts, noisy)
                self.record('', noisy)
                self.log[iteration]['Unassigned Analysts'] = unassigned_analysts
                converged = False
            else:
                self.record('At last! Convergence.', noisy)
                self.record('\nTiebreakers Used: {}'.format(str(self.random_tbs)),
                            noisy)
                if self.random_tbs:
                    self.record(self.random_tbs_data, noisy)
                converged = True
            self.log[iteration]['Converged'] = converged
            i += 1
        return placements

def random_schema(n_analysts, n_teams, extra_spots):
    '''Create a random Schema, with random names, teams, and other variables.
    n_analysts: (int) The number of analysts.
    n_teams: (int) The number of teams.
    extra_spots: (int) The number of additional spots beyond the minimum
        possible (i.e. the number of analysts.)
    '''
    MAX_PERF = 5
    MAX_RATING = 5
    CLASSES = [1,2,3]

    teams_path = "teams.csv"
    allnames = names.words('male.txt') + names.words('female.txt')
    teams = pd.read_csv(teams_path, header=None)[0].to_list()
    assert n_teams <= len(teams), 'Too many teams.'
    assert extra_spots >= 0, 'Invalid number.'

    rand_names = random.sample(allnames, n_analysts)
    rand_teams = random.sample(teams, n_teams)

    analysts = []
    for name in rand_names:
        rand_perf = random.randint(1, MAX_PERF)
        rand_class = random.sample(CLASSES, 1)[0]
        rand_team_order = random.sample(rand_teams, len(rand_teams))
        rand_prefs = {}
        for i, team in enumerate(rand_team_order):
            rand_prefs[team] = i
        analyst = Analyst(name, rand_class, rand_perf, rand_prefs)
        analysts.append(analyst)

    teams = []
    for team_name in rand_teams:
        rand_ratings = {}
        for analyst in rand_names:
            rand_ratings[analyst] = random.randint(1, MAX_RATING)
        team = Team(team_name, 1, rand_ratings)
        teams.append(team)

    total_spots = n_analysts + extra_spots
    remaining_spots = total_spots - n_teams
    for i in range(remaining_spots):
        rand_index = random.randint(0, n_teams-1)
        teams[rand_index].headcount += 1

    schema = Schema(analysts, teams)
    return schema

def read_excel(fp, analyst_sheet, team_sheet, name_col=1, class_col=2,
               perf_col=3, prefs_col_start=4, prefs_col_end=6, team_col=0,
               headcount_col=1, ratings_col_start=None, ratings_col_end=None):
    '''Processes an Excel file of analyst/team data into a Schema object.
    fp: (str) Excel File path
    analyst_sheet: Name of the sheet containing analyst data.
    team_sheet: Name of the sheet containing team data. Optional.
    '''
    clas_lambda = lambda x: int(x[-1])
    perf_map = {'Top': 4, 'Exceeds': 3, 'Meets': 2, 'Low': 1}
    perf_lambda = lambda x: perf_map[x]

    pref_col_range = [i for i in range(prefs_col_start, prefs_col_end+1)]
    n_pref_cols = prefs_col_end - prefs_col_start
    cols_to_keep = [name_col] + [class_col] + [perf_col]+ pref_col_range
    analyst_df = pd.read_excel(fp, analyst_sheet)
    analyst_df = analyst_df.iloc[:,cols_to_keep]
    overwrite_cols = ['Name', 'Class', 'Performance'] + [i for i in range(n_pref_cols+1)]
    analyst_df.columns = overwrite_cols
    analysts_dict = analyst_df.to_dict(orient='rows')

    analysts = []
    for analyst in analysts_dict:
        name = analyst['Name']
        clas = clas_lambda(analyst['Class'])
        perf = perf_lambda(analyst['Performance'])
        prefs = {str(v):k for k,v in analyst.items() if k not in ('Name', 'Class')}
        new_analyst = Analyst(name, clas, perf, prefs)
        analysts.append(new_analyst)

    cols_to_keep = [team_col] + [headcount_col]
    team_df = pd.read_excel(fp, team_sheet)
    team_df.iloc[:,cols_to_keep]
    overwrite_cols = ['Team', 'Headcount']
    team_df.columns = overwrite_cols
    team_dict = team_df.to_dict(orient='rows')

    teams = []
    for team in team_dict:
        name = str(team['Team']) #str() because 42
        headcount = team['Headcount']
        new_team = Team(name, headcount)
        teams.append(new_team)

    schema = Schema(analysts, teams)
    return schema

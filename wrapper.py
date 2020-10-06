from core import *

if __name__ == '__main__':
    fp = input('\nEnter Excel file path:\n')
    analyst_sheet = input('\nEnter analyst sheet:\n')
    if len(analyst_sheet): analyst_sheet = int(analyst_sheet)
    team_sheet = input('\nEnter team sheet:\n')
    if len(team_sheet): team_sheet = int(team_sheet)

    defaults = input('\nRead default columns? (y/n):\n')[0].lower()
    defaults = defaults == 'y'
    if defaults:
        schema = read_excel(fp, analyst_sheet, team_sheet)
    else:
        print('Not ready for that yet. Chill!')

    placements = schema.set_placements(noisy=True)

    placements_dicts = []
    for team in placements.keys():
        analysts = placements[team]
        for analyst in analysts:
            mini_dict = {'Analyst': analyst.name, 'Team': team}
            placements_dicts.append(mini_dict)

    placements_df = pd.DataFrame(placements_dicts)
    placements_df.to_csv('Upward_Placements.csv', index=False)
    log_fp = 'Upward_Placements_Log.txt'
    with open(log_fp, 'w') as file:
        file.write(schema.log_txt)

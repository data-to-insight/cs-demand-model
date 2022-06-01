MAX_YEARS_OF_DATA = 5

NOT_IN_CARE = 'Not in care'

ACCEPTED_DATE_FORMATS = ('%d/%m/%Y', '%Y-%m-%d')

table_headers = {
    'Episodes':
        'CHILD,DECOM,RNE,LS,CIN,PLACE,PLACE_PROVIDER,DEC,REC,REASON_PLACE_CHANGE,HOME_POST,PL_POST'.split(','),
    'Header':
        'CHILD,SEX,DOB,ETHNIC,UPN,MOTHER,MC_DOB'.split(',')
}

age_brackets = {
    '-1 to 1': ('Foster', 'Other'),
    '1 to 5': ('Foster', 'Other'),
    '5 to 10': ('Foster', 'Resi', 'Other'),
    '10 to 16': ('Foster', 'Resi', 'Other'),
    '16 to 18': ('Foster', 'Resi', 'Supported', 'Other'),
}

cost_params_map = {
    'Fostering (friend/relative)': ('Fostering', 'Friend/relative'),
    'Fostering (in-house)': ('Fostering', 'in-house'),
    'Fostering (IFA)': ('Fostering', 'IFA'),
    'Residential (in-house)': ('Residential', 'In-house'),
    'Residential (external)': ('Residential', 'External'),
    'Supported': ('Supported', 'Supported'),
    'Secure home': ('Other', 'Secure home'),
    'Placed with family': ('Other', 'Placed with family'),
    'Other': ('Other', 'Other')
}

next_brackets = {
    '-1 to 1': '1 to 5',
    '1 to 5': '5 to 10',
    '5 to 10': '10 to 16',
    '10 to 16': '16 to 18',
    '16 to 18': None,
}


class UploadError(Exception):
    pass

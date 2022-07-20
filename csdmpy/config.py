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

next_brackets = {
    '-1 to 1': '1 to 5',
    '1 to 5': '5 to 10',
    '5 to 10': '10 to 16',
    '10 to 16': '16 to 18',
    '16 to 18': None,
}
cost_params_map = {
    'foster_friend_relative': ('Foster', 'Friend/relative'),
    'foster_in_house': ('Foster', 'in-house'),
    'foster_IFA': ('Foster', 'IFA'),
    'resi_in_house': ('Resi', 'In-house'),
    'resi_external': ('Resi', 'External'),
    'supported_supported': ('Supported', 'Supported'),
    'other_secure_home': ('Other', 'Secure home'),
    'other_placed_with_family': ('Other', 'Placed with family'),
    'other_other': ('Other', 'Other')
    # NB the I in Resi's in-house is capitalised to prevent it from cancelling out with the in-house of Foster placements.
}
all_zero_props = {
    'foster_friend_relative': 0,
    'foster_in_house': 0,
    'foster_IFA': 0,
    'resi_in_house': 0,
    'resi_external': 0,
    'supported_supported': 0,
    'other_secure_home': 0,
    'other_placed_with_family': 0,
    'other_other': 0
}
class UploadError(Exception):
    pass

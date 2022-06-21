MAX_YEARS_OF_DATA = 2

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
    'Fostering (friend/relative)': ('Foster', 'friend/relative'),
    'Fostering (in-house)': ('Foster', 'in_houseF'),
    'Fostering (IFA)': ('Foster', 'IFA'),
    'Residential (in-house)': ('Resi', 'in_houseR'),
    'Residential (external)': ('Resi', 'external'),
    'Supported': ('Supported', 'supported'),
    'Other (secure-home)': ('Other', 'secure_home'),
    'Other (placed-with-family)': ('Other','with_family'),
    'Other (other)': ('Other','other')
}
# Conversion rules:
# Outer keys start with a capital letter and inner keys are all lowercase.
# All hyphens are replaced with underscores.

class UploadError(Exception):
    pass

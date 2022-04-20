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
    (-1, 1): ('Foster', ),
    (1, 5): ('Foster', ),
    (5, 10): ('Foster', 'Resi'),
    (10, 16): ('Foster', 'Resi'),
    (16, 18): ('Foster', 'Resi', 'Supported'),
}

class UploadError(Exception):
    pass

from .query import Query, QueryArgument

what = QueryArgument('q', str, disp_name='What')
where = QueryArgument('l', str, required=True, disp_name='Where')
radius = QueryArgument('radius', int, choices=(0, 5, 10, 15, 25, 50, 100), disp_name="Miles away")
min_salary = QueryArgument('q', int, fmt="${}", disp_name="Minimum Salary")
company = QueryArgument('rbc', str, requires='jcid', disp_name="Compay Name")
company_id = QueryArgument('jcid', str, requires='rbc', disp_name="Company id")
job_type = QueryArgument('jt', str, choices=('fulltime', 'parttime', 'contract', 'internship', 'temporary', 'commission'), disp_name="Job Type")
experience = QueryArgument('explvl', str, choices=('entry_level', 'mid_level', 'senior_level'), disp_name="Experience Level")
start = QueryArgument('start', int, disp_name="start")

class SimpleIndeedQuery(Query):
    _kwargs = {
        'what' : what,
        'where' : where,
        'radius' : radius,
        'min_salary' : min_salary,
        'company' : company,
        'company_id' : company_id,
        'job_type' : job_type,
        'experience' : experience,
        'start' : start
    }
    def __init__(self, **kwargs):
        super(SimpleIndeedQuery, self).__init__('https://indeed.com/jobs', **SimpleIndeedQuery._kwargs)
        self._init_kwargs(**kwargs)
    
    def _init_kwargs(self, **kwargs):
        for key, val in kwargs.items():
            if key in SimpleIndeedQuery._kwargs:
                self._args[key].value = val
            else:
                raise NotImplementedError("The following keyword is not valid for the SimpleIndeedQuery: %s"%key)


#Search Strings
all_of_these_words = QueryArgument('as_and', str, disp_name='All of these words')
exact_phrase = QueryArgument('as_phr', str, disp_name='Exact phrase')
any_of_these_words = QueryArgument('as_any', str, disp_name="Any of these words")
none_of_these_words = QueryArgument('as_not', str, disp_name="None of these words")
title_words = QueryArgument('as_ttl', str, disp_name="These words in title")
from_company = QueryArgument('as_cmp', str, disp_name="From this company")
from_this_job_site = QueryArgument('as_src', str, disp_name="From this job site")

#Ad Origin
posted_to = QueryArgument('st', str, choices=('jobsite', 'employer'), disp_name="Posted to")
hired_by = QueryArgument('sr', str, choices=('directhire',), disp_name="Who handles hiring")

#Sort and paging
sort_by = QueryArgument('sort', str, choices=('date',), disp_name="Sort by")
limit = QueryArgument('limit', int, choices=(10, 20, 30, 50), disp_name="Per Page")

#Age
from_age = QueryArgument('fromage', choices=('last', 1, 3, 7, 15, 'any'), disp_name="Max days old")

#Magic Args
psf = QueryArgument('psf', str, required=True, value='advsrch', mutable=False, requires='from')
searched_from = QueryArgument('from', str, required=True, value='advancedsearch', mutable=False, requires='psf')

class AdvancedIndeedQuery(Query):
    _kwargs = {
        'where' : where,
        'radius' : radius,
        'min_salary' : min_salary,
        'job_type' : job_type,
        'experience' : experience,
        'start' : start,
        'all_words' : all_of_these_words,
        'exact_phrase' : exact_phrase,
        'any_words' : any_of_these_words,
        'none_words' : none_of_these_words,
        'title_words' : title_words,
        'from_company' : from_company,
        'from_job_site' : from_this_job_site,
        'posted_to' : posted_to,
        'hired_by' : hired_by,
        'sort_by' : sort_by,
        'limit' : limit,
        'age' : from_age,
        'psf' : psf,
        'searched_from': searched_from
    }
    def __init__(self, **kwargs):
        super(AdvancedIndeedQuery, self).__init__('https://indeed.com/jobs', **AdvancedIndeedQuery._kwargs)
        self._init_kwargs(**kwargs)
    
    def _init_kwargs(self, **kwargs):
        for key, val in kwargs.items():
            if key in AdvancedIndeedQuery._kwargs:
                self._args[key].value = val
            else:
                raise NotImplementedError("The following keyword is not valid for the AdvancedIndeedQuery: %s"%key)
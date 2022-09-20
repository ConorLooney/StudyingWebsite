def contains_filter(property, value):
    return value in property

def equals_filter(property, value):
    return value == property

def apply_filter(terms, attribute, filter_value=None, filter_function=contains_filter):
    if filter_value is None:
        return terms
    new = []
    for term in terms:
        print(term[attribute])
        print(filter_value)
        if filter_function(term[attribute], filter_value):
            new.append(term)
    return new

def handle_search(request_form):
    search_term = request_form["search_field"]
    search_criteria = request_form["search_criteria"]
    if search_criteria == "equals":
        search_function = equals_filter
    elif search_criteria == "contains":
        search_function = contains_filter
    return search_term, search_function
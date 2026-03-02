
def safe_retrieve(retrieve_func, query):
    try:
        result = retrieve_func(query)
        return result if result else ""
    except Exception:
        return ""

def evaluate_response(question: str, response: str):
    """
    Score simple basé sur longueur.
    En vrai tu pourrais :
    - utiliser LLM-as-judge
    - comparer à une ground truth
    """

    if len(response) > 30:
        return 1
    return 0 
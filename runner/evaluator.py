import re

def evaluate_response(ai_response, correct_answer_index):
    """
    Compare la réponse de l'IA avec l'index de la bonne réponse.
    ai_response: texte généré (ex: "The correct choice is 3")
    correct_answer_index: int (ex: 3)
    """
    
  
    match = re.search(r'\d', str(ai_response))
    
    if match:
        extracted_answer = match.group()
       
        if extracted_answer == str(correct_answer_index):
            return 10  
        else:
            return 0   
            
  
    return 0
# Dictionary for mapping rejection reasons
REJECTION_REASONS_MAP = {
    "fake_document": "Fake_document",
    "not_covered": "Not_Covered",
    "policy_expired": "Policy_expired"
}

# Function to handle errors
def handle_error(error_message):
    print(f"Error: {error_message}")
    return "Error"

# Function to check if a rejection reason is present in text
def contains_rejection_reason(rejection_text, reason):
    try:
        if rejection_text and isinstance(rejection_text, str):
            return reason.lower() in rejection_text.lower()
        return False
    except Exception as e:
        handle_error(f"Error in contains_rejection_reason: {str(e)}")
        return False

# Function to map rejection text to a class
def map_rejection_reason(rejection_text):
    try:
        if not rejection_text or not isinstance(rejection_text, str):
            return "NoRemark"
        for reason, rejection_class in REJECTION_REASONS_MAP.items():
            if contains_rejection_reason(rejection_text, reason):
                return rejection_class
        return "Unknown"
    except Exception as e:
        handle_error(f"Error in map_rejection_reason: {str(e)}")
        return "Error"

# Function to classify rejection remarks
def complex_rejection_classifier(remark_text):
    try:
        if not remark_text or not isinstance(remark_text, str):
            return "NoRemark"
        if len(remark_text.strip()) == 0:
            return "NoRemark"
        
        # Check for each rejection reason
        for reason, rejection_class in REJECTION_REASONS_MAP.items():
            if contains_rejection_reason(remark_text, reason):
                return rejection_class
        return "Unknown"
    except Exception as e:
        handle_error(f"Error in complex_rejection_classifier: {str(e)}")
        return "Error"
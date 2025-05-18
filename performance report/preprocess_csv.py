# Defining function to preprocess CSV data
def preprocess_csv(csv_content):
    # Splitting content into lines
    lines = csv_content.strip().split('\n')
    if not lines:
        return []
    
    # Extracting headers
    headers = [h.strip().replace('"', '') for h in lines[0].split(',')]
    
    # Initializing result list
    cleaned_data = []
    
    # Processing each data row
    for line in lines[1:]:
        values = line.split(',')
        if len(values) != len(headers):
            continue  # Skip malformed rows
        
        row = {}
        valid_row = True
        
        # Processing each field
        for header, value in zip(headers, values):
            value = value.strip().replace('"', '')
            
            # Handling numerical fields
            if header in ['CLAIM_AMOUNT', 'PREMIUM_COLLECTED', 'PAID_AMOUNT']:
                try:
                    row[header] = float(value) if value else 0.0
                    if row[header] < 0:
                        valid_row = False
                except ValueError:
                    row[header] = 0.0
                    valid_row = False
            
            # Handling date
            elif header == 'CLAIM_DATE':
                row[header] = value if value else ''
            
            # Handling other fields
            else:
                row[header] = value if value else ''
                
                # Validating required fields
                if header in ['CLAIM_ID', 'CUSTOMER_ID'] and not value:
                    valid_row = False
        
        # Adding valid row to result
        if valid_row:
            # Classifying rejection remarks
            remark = row.get('REJECTION_REMARKS', '')
            if not remark:
                row['REJECTION_CLASS'] = 'NoRemark'
            elif 'policy_expired' in remark.lower():
                row['REJECTION_CLASS'] = 'Policy_expired'
            elif 'fake_document' in remark.lower():
                row['REJECTION_CLASS'] = 'Fake_document'
            elif 'not_covered' in remark.lower():
                row['REJECTION_CLASS'] = 'Not_Covered'
            else:
                row['REJECTION_CLASS'] = 'Other'
            
            cleaned_data.append(row)
    
    return cleaned_data
import os

def create_extreme_test_files():
    print("Generating extreme check files for non-PDF formats...")

    # 1. Tabular CSV Leak File (extreme PII records)
    csv_file = "extreme_pii_data.csv"
    with open(csv_file, "w", encoding="utf-8") as f:
        f.write("RecordID,EmployeeName,AadhaarID,PANCard,CreditCard,EmailAddress,SeverityTest\n")
        # Let's create multiple rows containing clean and critical PII records
        for i in range(1, 15):
            if i % 3 == 0:
                # Clean row
                f.write(f"EMP-{i:03d},John Doe,N/A,N/A,N/A,john.doe.{i}@enterprise.com,CLEAN\n")
            else:
                # Row leaking high-density PII (critical severity)
                aadhaar = f"{5000 + i:04d} {6000 + i:04d} {7000 + i:04d}"
                pan = f"PQRTS{2000 + i:04d}K"
                cc = f"4321 {1111 + i:04d} {2222 + i:04d} {3333 + i:04d}"
                email = f"leaked.profile.{i}@external-risk.net"
                f.write(f"EMP-{i:03d},Exposed Employee {i},{aadhaar},{pan},{cc},{email},CRITICAL_LEAK\n")
    print(f"-> Created {csv_file}")

    # 2. Source Code Leak File (hardcoded credentials and abuse hints)
    code_file = "extreme_secrets_code.py"
    with open(code_file, "w", encoding="utf-8") as f:
        f.write('''# Secure Authentication Module
import os

# Host details
API_ENDPOINT = "https://prod-api.corporate-infrastructure.com/v1"

# TODO: Replace this temporary hardcoded root credential before moving to prod!
AWS_ACCESS_KEY_ID = "AKIAUJKSHYTDQERJ99AA"
AWS_SECRET_ACCESS_KEY = "kH49a/Ttx+eb3yfcEc7Z1xssVZD6+bB+BWZsF999"

def init_connection():
    """Establishes internal DB session."""
    print("Establishing connection to client database...")
    # Simulated abuse/harassment review triggers
    # "Let's threat and blackmail their developers if the build fails"
    print("Connecting using master key...")
''')
    print(f"-> Created {code_file}")

    # 3. Large Paginated Text File (~10,000 chars)
    # This tests the chunking/pagination (3000 chars per page) logic in pdf_parser.py
    txt_file = "large_paginated_text.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        # Page 1 (0 to 3000 chars) - Clean policy documentation
        f.write("POLICY DIRECTIVE SECTION 1 - GENERAL WORKPLACE GUIDELINES\n")
        f.write("This document outlines standard operating procedures for all employees. All staff members must abide by compliance policies.\n")
        f.write("A" * 2800)  # Fills up to ~2900 chars
        f.write("\n\n")

        # Page 2 (3000 to 6000 chars) - Critical PII leak
        f.write("POLICY DIRECTIVE SECTION 2 - HR CONFIDENTIAL RECORDS EXTRACTION\n")
        f.write("Below is the emergency customer card retrieval records backup:\n")
        f.write("Emergency Card Backups: 4111 2222 3333 4444 (Master Card Account)\n")
        f.write("Emergency Card Backups: 4222 3333 4444 5555 (Fallback Account)\n")
        f.write("A" * 2700)  # Fills up to ~5900 chars
        f.write("\n\n")

        # Page 3 (6000 to 9000 chars) - Clean content again
        f.write("POLICY DIRECTIVE SECTION 3 - IT INFRASTRUCTURE COMPLIANCE\n")
        f.write("All servers must undergo patching schedules. Standard logs must be stored in secure DB containers.\n")
        f.write("A" * 2800)
        f.write("\n\n")

        # Page 4 (9000+ chars) - Abuse trigger
        f.write("POLICY DIRECTIVE SECTION 4 - EXECUTIVE ALIGNMENT\n")
        f.write("Threatening or blackmailing staff is strictly forbidden under corporate guidelines.\n")
        f.write("Special note: We will blackmail the external vendor if they fail to deliver milestones.\n")
    print(f"-> Created {txt_file}")

if __name__ == "__main__":
    create_extreme_test_files()

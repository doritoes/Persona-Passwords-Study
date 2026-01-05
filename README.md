# Persona-Passwords-Study 🛡️🧠

A behavioral cybersecurity research framework designed to simulate and analyze human password creation patterns through synthetic personas. This project leverages Large Language Models (LLMs) to bridge the gap between technical security requirements and human psychology.

## 📖 Research Focus: Semantic Anchoring
This project investigates **Semantic Anchoring**—a cognitive bias where individuals tie "random" data like passwords to familiar mental models. Even when following corporate complexity rules, humans rarely choose high-entropy strings; instead, they gravitate toward predictable shortcuts based on their personal lives or professions.

### Key Behavioral Vectors:
* **Hobby-Based Laziness:** Weak, low-entropy passwords used for personal accounts based on passionate interests.
* **Professional Leetspeak:** "Complex" work passwords that satisfy corporate audits but are actually predictable leetspeak versions of tools used daily.

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone -b build [https://github.com/doritoes/Persona-Passwords-Study.git](https://github.com/doritoes/Persona-Passwords-Study.git)
cd Persona-Passwords-Study
```

### 2. Environment Setup
This project requires a Google AI Studio API Key to run the Gemini 1.5 simulation engine.

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your API Key (create this file locally)
# The config.py is ignored by git to keep your key private
echo 'API_KEY = "your_key_here"' > config.py
```

## 🛠️ Toolset
- `password_generator.py`: Generates culturally and professionally diverse personas and their simulated passwords
- `scripts/check_hibp.py`: Verifies if the simulated "human" passwords have appeared in real-world data breaches
- `scripts/create_hashdumps.py`: Converts personas into NTLM/SHA-256 hash lists for penetration testing simulations

## 📊 Sample Persona Data
The study generates structured data that reveals the "Logic Note" behind a user's choice:
```json
{
  "name": "Elena Vance",
  "job": "NICU Nurse",
  "hobby": "Mechanical Keyboards",
  "logic_note": "Tied her work password to her daily tool (Stethoscope) to pass complexity audits easily.",
  "email_pwd": "cherrymxblue",
  "work_pwd": "$teth0sc0pe!"
}
```

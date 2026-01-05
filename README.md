# Persona-Passwords-Study 🛡️🧠

A behavioral cybersecurity study using Large Language Models (LLMs) to simulate human password generation. This project explores the tension between personal identity (hobbies) and security requirements (leetspeak/complexity) through synthetic personas and behavioral profiling.

## 📖 Project Overview

Humans rarely create truly random passwords. Instead, they use "semantic anchors"—personally meaningful words or professional tools—to satisfy security requirements while maintaining memorability. This repository contains the tools and research data used to simulate these behaviors across different AI architectures.

### Research Goals:
* **Hobby Anchoring:** Quantifying how often personal interests drive "lazy" email passwords.
* **Professional Shortcuts:** Analyzing the predictability of leetspeak-modified professional tools (e.g., `Stetho$cope1`).
* **Architectural Benchmarking:** Comparing the behavioral "reasoning" capabilities of local Edge-AI (NPU) vs. Cloud-based LLMs.

## 🛠️ Evolution of Methodology
This project began as a local hardware study using **OpenVINO** and the **NPU (Neural Processing Unit)** on a mobile workstation. It continues using cloud AI models.

### Phase 1: Local Edge-AI (Qwen-1.5B)
Initially, we attempted to use Qwen-1.5B via `openvino_genai`. This phase revealed significant **Instruction Collapse** in small models; the model struggled to maintain complex JSON structures while simultaneously inventing unique personas, often defaulting to generic tokens (e.g., "John Smith").

### Phase 2: Cloud-Based Reasoning (Gemini 2.5 Flash)
To achieve higher behavioral fidelity, the study pivoted to the **Gemini API**. This allowed for:
* **Native JSON Output:** Reliable structured data without parsing errors.
* **Diverse Identities:** Greater cultural and professional variety in generated personas.
* **Deep Reasoning:** High-quality "logic notes" explaining the simulated user's choices.

Using gemini.google.com to build prompts led to a variety of caricatures of human behavor. Essentially the study is a "mirror of a mirror", according to Gemini itself. It is a struggle to get natural behavior.

## 🚀 Getting Started
### Prerequisites
* Python 3.10+
* Google AI Studio API Key (Free Tier)
* (Optional) OpenVINO Toolkit for local NPU experiments

### Installation
1.  Clone the repository:
    ```bash
    git clone [https://github.com/YOUR_USERNAME/Persona-Passwords-Study.git](https://github.com/YOUR_USERNAME/Persona-Passwords-Study.git)
    cd Persona-Passwords-Study
    ```
2.  Install dependencies:
    ```bash
    pip install -U google-generativeai
    ```
3.  Set up your API Key:
    * Create a `config.py` (added to `.gitignore`) and add: 
        `API_KEY = "your_key_here"`

## 📊 Data Format
The generated study data is saved in JSON format with the following schema:
```json
{
  "name": "Full Name",
  "job": "Occupation",
  "hobby": "Personal Interest",
  "logic_note": "Reasoning for password choices",
  "email_pwd": "Hobby-based password",
  "work_pwd": "Complex career-based password"
}
```

An additional credentials.csv is saved in CSV format
```csv
"name","user_id","password","type","sector","behavior"
```

## Status
The current prompt function gives some passable results. It is currently too focused on password reuse (personal to work password relationship), but this is an interesting field of study. The work passwords are checked for validity to 12+ chars and 3 of 4: Upper, Lower, Digit, Symbol

```python
def get_prompt(count, sector):
    return f"""
    Generate {count} unique personas for a study on password habits in the {sector} sector.

    RESEARCH FOCUS: Credential Reuse.
    - personal_password: Raw human root (hobbies, slang, swearing, pet names).
    - work_password: A modification of that root that is AT LEAST 12 characters
      and includes numbers and symbols (e.g., 'rootword' -> 'Rootword!2026').

    Return ONLY a raw JSON list:
    [{{"name":"", "occupation":"", "personal_email":"", "personal_password":"", "work_lanid":"", "work_password":"", "behavior_tag":""}}]
    """
```
## Next Steps
Start a new Gemini Conversation
1. add a blacklist of top 25 breached passwords to the password validation function
2. handle duplicate usernames
3. clean output to `credentials.csv` to just the username and password
4. full run 5000 personas which has 10000 user/pass combos
5. update `create_hashdumps.py` to generate based on the `credentials.csv` file
6. run `create_hashdumps.py` to create the hash files
7. create script to take random selections of each hash file, create the sample files for each hash type
8. run through password audit engine
9. take the cracked password list and analyze if there is a relation between the crack of personal vs work passwords; is there a relationship between the two?

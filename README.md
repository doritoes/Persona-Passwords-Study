# Persona-Passwords-Study 🛡️🧠
A behavioral cybersecurity study using Large Language Models (LLMs) to simulate human password generation. This project explores the tension between personal identity (hobbies) and security requirements (leetspeak/complexity) through synthetic personas and behavioral profiling.

## 📖 Project Overview
Humans rarely create truly random passwords. Instead, they use "semantic anchors". This involves personally meaningful words or to satisfy security requirements while maintaining memorability. This repository contains the tools and research data used to simulate these behaviors.

NOTE The key focus is not simulating the full human password selection process, but how "compliant" password may be related to the same "root" used for less complex passwords. The implications of this are that the compromise of "less important/less secure sites or systems" may be used to effectively large the same individual's "more secure" password.

### Research Goals:
* **Hobby Anchoring:** Quantifying how often personal interests drive "lazy" email passwords.
* **Professional Shortcuts:** Analyzing the predictability of leetspeak-modified professional tools (e.g., `Stetho$cope1`).
* **Architectural Benchmarking:** Comparing the behavioral "reasoning" capabilities of local Edge-AI (NPU) vs. Cloud-based LLMs.
* **Diversity Challenges:** The LLM likes to keep picking the same names and data over and over. In synthetic data generation, around the 1500-2000 mark "token exhaustion" kicks in. Even with high heath and random seeds (used here) LLMs tend to drift back to their most statistically probable "global" names (the David Smiths and Maria Garcias of the world) once the low-hanging fruit is gone.

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

### Start Creating Data
1. `password_generator.py`
    - creates `personas.json`
    - creates `credentials.csv`
    - creates `data_summary.txt`
    - Review these files while the code runs
        - `watch -d 'cat data_summary.txt;'`
    - Note as the Gemini model struggles to come up with more unique personas
        - Duplicate personas: same name, rejected by script
        - Non-unique personal passwords: allowed by script, note similar common rules in actual password dumps
        - Non-unique work passwords: allowed by script, note it's less common than for personal passwords; if this starts creeping up, the model has got stuck in a loop doing the same transformations every time
2. check_hibp.py
3. create_hashdumps.py

### Start Analyzing the Data and Cracking Results

## 📊 Data Format
The generated study data is saved in JSON format with the following schema:
```json
{
  "name": "Full Name",
  "occupation": "Occupation",
  "personal_email": "Personal Interest",
  "personal_password": "Reasoning for password choices",
  "work_lanid": "Hobby-based password",
  "work_password": "Complex career-based password",
  "behavior_tag": "How the root (personal password) was transformed to be come the work password",
  "sector": "The name of the sector provided in the prompt"
}
```

An additional credentials.csv is saved in CSV format
```csv
"user_id","password"
```

## Status
The current prompt function gives some passable results. It is currently too focused on password reuse (personal to work password relationship), but this is an interesting field of study. The work passwords are checked for validity to 12+ chars and 3 of 4: Upper, Lower, Digit, Symbol. Duplicate personas are prevented from being collected in the output.

```python
def get_prompt(count, sector):
    batch_seed = uuid.uuid4().hex[:8]
    return f"""
    Generate {count} unique personas for a study on password habits in the {sector} sector.
    Batch Seed: {batch_seed} (Internal entropy seed).
    RESEARCH FOCUS: Credential Reuse.
    - Diversity: Global mix of names and backgrounds.
    - personal_password: Raw human root (hobbies, slang, pet names).
    - work_password: A modification of that root (12+ chars, numbers, symbols).
    Return a JSON list of objects: name, occupation, personal_email, personal_password, work_lanid, work_password, behavior_tag
    """
```

## Next Steps
1. update `check_hibp.py` to check the passwords in credentials.csv against HIBP, output csv with additional column indicated if pwned
2. ensure the script can handle throttling by google in case it happens
3. full run 2500 personas which has 5000 user/pass combos
4. update `create_hashdumps.py` to generate based on the `credentials.csv` file
5. run `create_hashdumps.py` to create the hash files
6. create script to take random selections of each hash file, create the sample files for each hash type
7. run through password audit engine
8. expand on CSV file with column "was cracked"
9. take the cracked password list and analyze if there is a relation between the crack of personal vs work passwords; is there a relationship between the two?
10. analyze top behavior tags, top tags per sector, per occupation
11. analyze crack rate per sector vs published rates per sector; also crack rates per profession; also crack rates per behavior tag
12. Analys of HIBP coverage, HIBP vs cracked

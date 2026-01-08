# Persona-Passwords-Study 🛡️🧠
A behavioral cybersecurity study using Large Language Models (LLMs) to simulate human password generation. This project explores the tension between personal identity (hobbies) and security requirements (leetspeak/complexity) through synthetic personas and behavioral profiling.

NOTE If you are looking for sample dataset, see [Sample Dataset](scripts/sample/README.md]

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
* **Deep Reasoning:** High-quality "behavior tag" explaining the simulated user's choices.

Using gemini.google.com to build prompts led to a variety of caricatures of human behavor. Essentially the study is a "mirror of a mirror", according to Gemini itself. It is a struggle to get natural behavior.

Key learnings
* Used seeds (job sector, and unique UUID-based seed) to increase diversity of personas created (less duplicates)
* Higher temperature and batch sizes improved diversity and reduced duplicates but produced more invalid JSON; used JSON data salvage function to extract the usable data
* Detected and ignored duplicate personas (names)


## 🚀 Getting Started
### Prerequisites
* Python 3.10+
* Google AI Studio API Key (Tier 1)
  * https://ai.google.dev/gemini-api/docs/pricing#gemini-2.5-flash
  * Free tier limited to 2 requests per minute/20 requests per day
  * Note that Gemini 2.5 Flash-Lite free limit is 30 RPM, 1,500 RPD
  * All the good free tiers are gone
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
    - Without arguments, bases personas on a rotating list of "Sectors" of the workforce
    - Optionally provide a sector name to study it exclusively
        - Ex. `python3 password_generator "Gig Economy"`
    - creates `personas.json`
    - creates `credentials.csv`
    - creates `data_summary.txt`
    - Review these files while the code runs
        - `watch -d 'cat data_summary.txt;'`
    - Note as the Gemini model struggles to come up with more unique personas
        - Duplicate personas: same name, rejected by script
        - Non-unique personal passwords: allowed by script, note similar common patterns in actual password dumps
        - Non-unique work passwords: allowed by script, note it's less common than for personal passwords; if this starts creeping up, the model has got stuck in a loop doing the same transformations every time
2. `check_hibp.py credentials.csv`
    - Checks the passwords in `credentials.csv` against HIBP
    - Outputs `checked_credentials.csv` with the enriched data
3. `create_hashdumps.py credentials.csv`
    - Creates `shadow.txt` with `/etc/shadow` values
    - Creates `pwdump.txt` with "pwdump" Windows hashes
    - Creates `md5.txt` with md5 hashes
    - Creates `sha1.txt` with sha1 hashes
    - Creates `sha256.txt` with SHA2-256 hashes
4. `sample.py 25% shadow.txt pwdump.txt md5.txt sha1.txt sha256.txt`
    - Takes a 25% randomized sample of the specified files
    - Outputs to new files that start with `sample_`
      - `sample_shadow.txt`
      - `sample_pwdump.txt`
      - `sample_md5.txt`
      - `sample_sha1.txt`
      - `sample_sha256.txt`

### Start Analyzing the Data and Cracking Results
Approaches taken:
- Gemini 2.5 Flash
  - performed much better in data quality over Gemini 2.0 Flash
  - had issues with creating valid JSON (had to include function to salvage valid JSON data and ignore the extraneous data)
  - temperature 0.7 is just high enough to trigger the invalid JSON, but it gave reasonable data quality (data interesting enough to study)
  - issue of receiving duplicate personas (well at least the name was duplicate) was managed by having high enough temperature and larger batch size ("CHUNK_SIZE")
  - issue of non-compliant work passwords was managed by validation functions
- Hashtopolis as a password auditing platform/cracking tool (running hashcat at scale)
  - Using onerule (rule) + rockyou (password list)
  - SHA512Crypt hashes (seen in the shadow file list) are very slow and resistent to cracking even with 6 GPU workers
  - HIBP found some passwords that hash cracking did not find
  - Personal passwords had a crack rate of 83% vs HIBP rate of 83%
  - Work passwords had a crack rate of 0%
    - One work password was in HIBP
    - Median work password length was 19, minimum 12, 3 of 4 character classes. Maximum length 34

On common roots: (the base string or idea that passwords are build around)
- Just like humans (based on data) seem to natually create clusters around certain roots, the AI model also had larger than expected clusters
- The process to expand to a more "work password" was complex enough that we there were only a 4 passwords that appeared more than once
- Identifing common roots in real life password dumps could greatly improve password guessing
- Understanding the real life personal behind a password can be very instructive in password guessing

On Pwned passwords:
- 84% of the "personal" passwords were in the HIBP database
  - Some funny passwords that weren't pwned
    - securempls
    - SiestaTime
    - mountainhike
- 1 (<0.1%) of the "work" passwords was in the HIBP database
  - in part due to the median "work" password length of 19 (minimum of 13)
  - in part due to the healthy adoption of symbols ("3 of 4 types" policy)

On cracked passwords:
- Similar rates of 83% for cracking and HIBP
- Example passwords not caught by either:
  - SoccerFanatics
  - TechGuru78
  - SiestaTime
  - HealthyPlate
- Example passwords missed by cracking but caught by HIBP
  - WinterIsComing and winteriscoming
  - gaelicpride
  - communityhealth
  - ikeafurniture
  - guinnesspint
  - kendochamp
- While no work password were cracked, one was found in HIBP
  - Ch3rryBl0ss0m!
- Examples of personal passwords that did well, not cracked or found in HIBP
  - MyKidsAreBest
  - TechGuru78
  - BigDataNerd
  - ExcelMaster
  - MyHeartBeat
  - FirstAidHere
  - SkiSlopes
  - accountingWhiz
  - diyexpert

Key Learnings:
- "3 of 4 character classes" was very effective, no need to require all 4 character classes

Interesting but requires further study:
- Deliberately mispelling words in passwords was not explored
- Passphrase initialisms were not explored (take a phrase from a saying or book, take the first letter of each word and form a password)
- Long passphrases were not explored
  - studying the more common long passphrases in breach dumps would be very instructive for auditing long passwords as well as creating potential initialisms for attack
- Using AI to extract the roots inside password dumps might highlight the more common roots to target for cracking

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
1. Analysis
    - analyze top behavior tags, top tags per sector, per occupation
    - analyze crack rate per sector vs published rates per sector; also crack rates per profession; also crack rates per behavior tag
    - analysis of HIBP coverage, HIBP vs cracked

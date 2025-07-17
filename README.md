# BlackRock Challenge Evaluator (v3)



This project automates the evaluation of Dockerized applications submitted for the BlackRock Retirement Savings Code Challenge.



## 📁 Folder Structure

- `evaluator_blackrock_v3.py` — Evaluation script

- `deliveries/` — Place Docker images or projects with Dockerfile here

- `logs/` — Evaluation logs per participant

- `test_cases/` — JSON files with expected input/output for each endpoint

- `shell_scripts/` — Bash scripts to build/load and run containers



## 🐳 Docker Submission Format

- The image must be named: `blk-hacking-mx-{first-last}`

- The application must expose 5 endpoints on port `5477` (internally runs on port `80`)

- Dockerfile must start with the build instruction



## ▶️ How to Run

```bash

&nbsp;python hkt-mx-evaluator-blk.py --dir "{Projects PATH}"

```

or just:

```bash

python hkt-mx-evaluator-blk.py

```

## ▶️ Output

- The script will create a `logs/` folder with evaluation results for each participant.

- Each log file will contain the results of the evaluation, including passed/failed test cases and any errors encountered.

- If any participant's submission fails to meet the requirements, it will be logged with an error message.

- The script will create a csv file named `hkt-mx-blk-results.csv` in the current directory, summarizing the evaluation results for all participants.



## ✅ Score

Each submission is evaluated using 5 test cases. Each passed test case contributes **20 points** (total: 100 points).

| Criteria         | Description                | Weight per Test Case |

|------------------|---------------------------|----------------------|

| HTTP 200         | Correct HTTP status code   | 0.3                  |

| JSON Structure   | Valid JSON structure       | 0.3                  |

| Valid Values     | Correct values in response | 0.4                  |



**Total per test case:** 20 points  

**Maximum total score:** 100 points

&nbsp;

## ▶️ Included Demo

A working demo project is available under:

```

deliveries/blk-hacking-mx-demo/

```



## 📦 Dependencies

- Python 3.x

- Docker installed and accessible from CLI

- Python packages:




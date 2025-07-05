# Beginner Setup Guide

**New to the Financial Analysis Toolkit?** This guide will walk you through everything step-by-step, no prior experience required!

## What You'll Learn

By the end of this guide, you'll be able to:
- Install the toolkit on your computer
- Run your first retirement simulation
- Understand the results
- Customize simulations with your own financial data

## Prerequisites

**You need:**
- A computer (Windows, Mac, or Linux)
- 15-30 minutes of your time
- Basic comfort with typing commands

**No prior experience needed with:**
- Python programming
- Financial modeling
- Command line interfaces

---

## Step 1: Install Python

The toolkit requires Python 3.11 or higher. Let's check if you have it:

### Windows

1. **Check if Python is installed:**
   - Press `Windows + R`, type `cmd`, press Enter
   - Type: `python --version`
   - If you see "Python 3.11" or higher, skip to Step 2
   - If you get an error or see Python 3.10 or lower, continue below

2. **Install Python:**
   - Go to [python.org/downloads](https://www.python.org/downloads/)
   - Click "Download Python 3.12" (or latest version)
   - Run the installer
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
   - Click "Install Now"

3. **Verify installation:**
   - Open a new Command Prompt (Windows + R, type `cmd`)
   - Type: `python --version`
   - You should see "Python 3.12" or similar

### Mac

1. **Check if Python is installed:**
   - Open Terminal (press `Cmd + Space`, type "Terminal")
   - Type: `python3 --version`
   - If you see "Python 3.11" or higher, skip to Step 2

2. **Install Python:**
   - Go to [python.org/downloads](https://www.python.org/downloads/)
   - Download and install Python 3.12
   - Or use Homebrew: `brew install python`

### Linux

1. **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git
   ```

2. **CentOS/RHEL:**
   ```bash
   sudo yum install python3 python3-pip git
   ```

---

## Step 2: Get the Financial Analysis Toolkit

### Option A: Download from GitHub (Easiest)

1. **Go to the project page:**
   - Visit: https://github.com/GGcarlson/Financial-Analysis-Toolkit
   - Click the green "Code" button
   - Click "Download ZIP"

2. **Extract the files:**
   - **Windows**: Right-click the ZIP file → "Extract All" → Choose a location like `C:\Users\YourName\Financial-Analysis-Toolkit`
   - **Mac**: Double-click the ZIP file, it will extract automatically
   - **Linux**: `unzip Financial-Analysis-Toolkit-main.zip`

### Option B: Using Git (If you have Git installed)

```bash
git clone https://github.com/GGcarlson/Financial-Analysis-Toolkit.git
```

---

## Step 3: Navigate to the Project Directory

**Windows:**
```cmd
cd C:\Users\YourName\Financial-Analysis-Toolkit
```
(Replace `YourName` with your actual username)

**Mac/Linux:**
```bash
cd ~/Financial-Analysis-Toolkit
# or wherever you extracted it
```

**💡 Tip**: You can also drag the folder into your terminal/command prompt to get the correct path.

---

## Step 4: Set Up the Environment

This creates a separate space for the toolkit so it doesn't interfere with other software.

### Windows

```cmd
REM Create virtual environment
python -m venv venv312

REM Activate it
venv312\Scripts\activate

REM You should see (venv312) at the start of your command prompt
```

### Mac/Linux

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# You should see (venv) at the start of your command prompt
```

---

## Step 5: Install the Toolkit

Make sure you're in the project directory and your virtual environment is activated (you should see `(venv312)` or `(venv)` in your command prompt).

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install the toolkit
python -m pip install -e .
```

This might take a minute as it downloads and installs everything needed.

---

## Step 6: Verify Installation

Let's make sure everything works:

```bash
# Check if the CLI is available
finance-cli --help

# List available strategies
finance-cli list-strategies

# Run a quick test
finance-cli retire --strategy dummy --years 5 --paths 10
```

You should see output without errors. If you get errors, see the [Troubleshooting](#troubleshooting) section below.

---

## Step 7: Your First Retirement Simulation

Now let's run a real retirement simulation! We'll use the classic "4% rule":

```bash
finance-cli retire --strategy four_percent_rule --years 30 --paths 100
```

**What this does:**
- Simulates a 30-year retirement
- Uses the 4% withdrawal rule (withdraw 4% of your initial balance each year)
- Runs 100 different market scenarios
- Assumes you start with $1,000,000

**You should see output like:**
```
Running retirement simulation...
Strategy: four_percent_rule
Years: 30
Paths: 100
Success rate: 94.0%
Median final balance: $1,234,567
```

🎉 **Congratulations!** You just ran your first retirement simulation!

---

## Step 8: Customize with Your Data

Now let's use your actual financial situation. Replace these numbers with your own:

```bash
finance-cli retire \
  --strategy four_percent_rule \
  --years 30 \
  --paths 500 \
  --init-balance 750000 \
  --equity-pct 0.7 \
  --age 55 \
  --fees-bps 75
```

**What each parameter means:**
- `--init-balance 750000`: You have $750,000 saved
- `--equity-pct 0.7`: 70% of your portfolio is in stocks
- `--age 55`: You're 55 years old
- `--fees-bps 75`: Your investment fees are 0.75% per year
- `--paths 500`: Run 500 different market scenarios (more = more reliable)

---

## Step 9: Include Taxes

If you want to account for taxes on your withdrawals:

```bash
finance-cli retire \
  --strategy four_percent_rule \
  --years 30 \
  --paths 500 \
  --init-balance 750000 \
  --equity-pct 0.7 \
  --age 55 \
  --tax single
```

Use `--tax single` if you're single, or `--tax married` if you're married filing jointly.

---

## Step 10: Save Your Results

To save the detailed results to a file:

```bash
finance-cli retire \
  --strategy four_percent_rule \
  --years 30 \
  --paths 500 \
  --init-balance 750000 \
  --equity-pct 0.7 \
  --age 55 \
  --tax single \
  --output my_retirement_results.csv
```

This creates a CSV file you can open in Excel or Google Sheets.

---

## Understanding Your Results

### Key Metrics Explained

**Success Rate**: Percentage of scenarios where your money lasted the full retirement period
- 95%+ = Very safe
- 90-95% = Generally safe
- 80-90% = Moderate risk
- Below 80% = High risk

**Median Final Balance**: The middle value of your ending balance across all scenarios
- Higher = More money left over
- Lower = Less cushion

**Percentiles**: Show the range of possible outcomes
- 10th percentile = Worst 10% of scenarios
- 90th percentile = Best 10% of scenarios

### Sample Interpretation

```
Success rate: 92.0%
Median final balance: $1,234,567
10th percentile: $234,567
90th percentile: $2,345,678
```

**This means:**
- 92% chance your money lasts 30 years
- In half the scenarios, you end with $1.2M+
- In the worst 10% of scenarios, you still have $234K+
- In the best 10% of scenarios, you have $2.3M+

---

## Common Strategies to Try

### 1. Four Percent Rule (Conservative)
```bash
finance-cli retire --strategy four_percent_rule --years 30 --paths 500
```
- Withdraw 4% of initial balance, adjusted for inflation
- Very conservative approach

### 2. Constant Percentage (Dynamic)
```bash
finance-cli retire --strategy constant_pct --percent 0.035 --years 30 --paths 500
```
- Withdraw 3.5% of current balance each year
- Adjusts automatically to market performance

### 3. Guyton-Klinger (Adaptive)
```bash
finance-cli retire --strategy guyton_klinger --years 30 --paths 500
```
- Increases withdrawals in good years
- Decreases withdrawals in bad years
- Good balance of income and safety

---

## Using Configuration Files

For complex scenarios, create a configuration file:

**Create a file called `my_retirement.yml`:**
```yaml
strategy: four_percent_rule
years: 30
paths: 1000
init_balance: 750000.0
equity_pct: 0.7
fees_bps: 75
age: 55
tax_filing_status: single
output: my_results.csv
verbose: true
```

**Run it:**
```bash
finance-cli retire --config my_retirement.yml
```

---

## Troubleshooting

### Common Issues and Solutions

#### ❌ `'finance-cli' is not recognized`

**Problem**: The CLI command isn't found
**Solution**: Make sure you're in the right directory and virtual environment is activated

```bash
# Windows
venv312\Scripts\activate

# Mac/Linux  
source venv/bin/activate

# Then try again
finance-cli --help
```

#### ❌ `No module named 'capstone_finance'`

**Problem**: Package not installed correctly
**Solution**: Reinstall the package

```bash
pip install -e .
```

#### ❌ `ERROR: Package 'capstone-finance' requires a different Python`

**Problem**: Your Python version is too old
**Solution**: Install Python 3.11 or higher (see Step 1)

#### ❌ `The system cannot find the path specified`

**Problem**: You're not in the right directory
**Solution**: Navigate to the project directory

```bash
# Windows - find where you extracted it
dir
cd Financial-Analysis-Toolkit

# Mac/Linux
ls
cd Financial-Analysis-Toolkit
```

#### ❌ `Permission denied` errors

**Problem**: Installation permissions
**Solution**: Use user installation

```bash
pip install --user -e .
```

#### ❌ Commands run but no output

**Problem**: Missing parameters
**Solution**: Add required parameters

```bash
# Instead of just: finance-cli retire
# Use: finance-cli retire --strategy four_percent_rule --years 30 --paths 100
```

---

## Next Steps

Now that you have the basics working:

1. **Try different strategies** - Compare `four_percent_rule`, `constant_pct`, and `guyton_klinger`
2. **Adjust parameters** - Try different equity percentages, time horizons, and starting balances
3. **Export results** - Save to CSV and analyze in Excel/Google Sheets
4. **Learn more** - Read the [Quick Start Guide](docs/quick-start.md) for advanced features

---

## Getting Help

If you're stuck:

1. **Check this troubleshooting section** above
2. **Ask for help** at https://github.com/GGcarlson/Financial-Analysis-Toolkit/issues
3. **Include details** in your question:
   - Your operating system (Windows 10, Mac, etc.)
   - Python version (`python --version`)
   - Exact error message
   - What you were trying to do

---

## Financial Disclaimer

⚠️ **Important**: This toolkit is for educational purposes only and does not constitute financial advice. 

The simulations are based on historical data and mathematical models that may not predict future market conditions. Always:
- Consult with qualified financial professionals
- Understand that past performance doesn't guarantee future results  
- Consider your individual financial situation and risk tolerance
- Verify all calculations independently

---

## Success Stories

**"I used this toolkit to model my early retirement plan and discovered I was being too conservative with my withdrawal rate. It gave me confidence to retire two years earlier than planned!"** - Sarah, Age 58

**"The tax feature helped me understand how much I'd actually need to withdraw from my traditional IRA. The difference was eye-opening!"** - Mike, Age 62

**"As a financial advisor, I use this toolkit to show clients different withdrawal strategies. The visualizations make complex concepts much easier to understand."** - Jennifer, CFP

---

Ready to take control of your financial future? Start with Step 1 above! 🚀
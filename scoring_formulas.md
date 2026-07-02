# ARIS Scoring and Ranking Formulations

This document provides a mathematical and logical reference for the formulas used in the **Candidate Scoring Engine** and **Candidate Ranking Engine**.

---

## 1. Overall Candidate Score

The overall score combines all candidate evaluation signals into a single role-aware score between $0.0$ and $100.0$. It is computed as a weighted average of active components and rounded to one decimal place:

$$\text{Overall Score} = \text{round}\left( \frac{\sum (S_c \times W_c)}{\sum W_c}, 1 \right)$$

Where:
- $S_c$ is the individual score of active component $c$ (scaled to $[0.0, 100.0]$).
- $W_c$ is the component weight configured by the target role's `EvaluationStrategy`.

---

## 2. Component Score Formulations ($S_c$)

### A. Skill Strength ($S_{skills}$)
Evaluates the candidate's top verified skills, filtering out common IDEs, tools, and editors to focus purely on technical capabilities.
1. Filter out candidate skills that match IDEs, editors, or tool keywords (e.g. *VS Code*, *PyCharm*, *Sublime Text*).
2. Sort the remaining skills by their numerical `confidence_score` (derived from the Skill Confidence Engine) in descending order.
3. Compute the average score of the top $K$ skills (where $K = \min(10, \text{number of remaining skills})$):
   $$S_{skills} = \text{round}\left( \frac{\sum_{i=1}^{K} \text{confidence\_score}_i}{K}, 1 \right)$$

### B. Experience Quality ($S_{experience}$)
Compares the total years of parsed professional experience against the job's minimum required years.
1. Convert each experience entry duration string (e.g., `'2 years'`, `'6 months'`) into float years:
   - Years matches are parsed directly.
   - Months matches are parsed and scaled by $\frac{1}{12}$.
   - Fallback: If no duration strings can be parsed but experience items exist, default to $1.0$ year per entry.
2. Sum all years to calculate total experience: $\text{total\_years} = \sum \text{parsed\_years}$.
3. Scale the ratio against the job requirements ($Y_{req}$, clamped to a minimum of $1.0$ year):
   $$S_{experience} = \text{round}\left( \min\left(100.0, \frac{\text{total\_years}}{\max(1.0, Y_{req})} \times 100.0\right), 1 \right)$$

### C. Achievement Impact ($S_{achievements}$)
Normalizes the raw standout achievement score (calculated by scanning candidate resumes for academic, technical, research, leadership, and entrepreneurship indicators) to a $100$-point scale.
$$S_{achievements} = \text{round}\left( \max(0.0, \min(10.0, A_{raw})) \times 10.0, 1 \right)$$
*Where $A_{raw}$ is the raw achievement score from the Standout Achievement Analyzer on a $[0.0, 10.0]$ scale.*

### D. Projects Strength ($S_{projects}$)
Evaluates the candidate's project portfolio based on quantity and technical relevance to the job's required skills.
1. Let $\text{total\_projects}$ be the total number of projects in the profile.
2. Let $\text{relevant\_projects}$ be the number of projects containing at least one technology matching the job's required skills.
3. Compute the score (each project adds $20\%$, and each relevant project adds an additional $20\%$ up to a maximum cap of $100.0$):
   $$S_{projects} = \min\left(100.0, (\text{total\_projects} \times 20.0) + (\text{relevant\_projects} \times 20.0)\right)$$

### E. Leadership Strength ($S_{leadership}$)
Evaluates lead roles and leadership achievements:
- If the candidate has held an explicit leadership role (e.g., role title contains `"lead"`, `"manager"`, `"head"`, `"director"`, `"founder"`, `"CTO"`, `"CEO"`), then:
  $$S_{leadership} = 100.0$$
- Otherwise, scale points using candidate's documented leadership achievements:
  $$S_{leadership} = \min\left(100.0, \text{leadership\_achievements} \times 50.0\right)$$

### F. Hard Requirements Compliance ($S_{hard\_requirements}$)
Derived from the compliance coverage score matching the candidate's capabilities (including inferred ancestors in the Skill Knowledge Graph) against the job's core criteria:
$$S_{hard\_requirements} = \text{round}\left( \text{coverage\_score} \times 100.0, 1 \right)$$

---

## 3. Deterministic Ranking & Tie-Breakers

When ranking a list of candidates, the **Candidate Ranking Engine** sorts them primarily by their `overall_score` (descending). 

In the event of a tie (multiple candidates having the exact same overall score), the engine resolves the ordering using a strict, multi-tiered tie-breaker hierarchy:

| Priority | Tie-Breaker Metric | Sort Order | Details / Rationale |
| :---: | :--- | :---: | :--- |
| **1** | **Overall Score** | Descending | Primary candidate match quality. |
| **2** | **Hard Requirements Coverage** | Descending | Prioritizes candidate matching critical prerequisites. |
| **3** | **Semantic Match Score** | Descending | Higher semantic alignment with role context. |
| **4** | **Average Skill Confidence Score** | Descending | Higher verified skills depth. |
| **5** | **Achievement Score** | Descending | Tie-breaker favoring standout candidate achievements. |
| **6** | **Candidate Name** | Ascending | Final deterministic alphabetical fallback. |

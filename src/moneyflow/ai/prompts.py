"""
Financial Analysis Prompt Templates
Pre-defined prompts for common financial queries
"""


class FinancialPrompts:
    """Collection of prompt templates for financial analysis"""

    @staticmethod
    def get_overview_prompt():
        """Get prompt for financial overview"""
        return """Give a friendly snapshot of my finances.

Format:
- One short verdict sentence
- 3 key observations, each under 18 words
- 2 practical next steps

Avoid long explanations. Use plain language and only the most useful numbers."""

    @staticmethod
    def get_budgeting_prompt():
        """Get prompt for budgeting advice"""
        return """Give simple budgeting advice from this data.

Format:
- One short summary sentence
- 3 budget adjustments worth making
- 1 category to watch
- 1 category that looks healthy

Keep it concise and practical. Do not create a long budget report."""

    @staticmethod
    def get_savings_prompt():
        """Get prompt for savings recommendations"""
        return """Find quick savings opportunities.

Format:
- 3 realistic savings ideas
- Estimated monthly saving for each, if the data supports it
- One easy first action

Keep the tone encouraging. Avoid generic advice and long descriptions."""

    @staticmethod
    def get_spending_pattern_prompt():
        """Get prompt for spending pattern analysis"""
        return """Analyze the spending patterns and provide insights on:
- Most frequent types of transactions
- Peak spending periods
- Recurring subscriptions and their value
- Unusual or one-time large expenses"""

    @staticmethod
    def get_recurring_bills_prompt():
        """Get prompt for recurring bills analysis"""
        return """Review the recurring transactions and subscriptions:
- List all recurring expenses with their frequency
- Identify potentially unnecessary subscriptions
- Suggest alternatives or ways to reduce these costs
- Calculate total annual cost of subscriptions"""

    @staticmethod
    def get_category_deep_dive_prompt(category):
        """Get prompt for category-specific analysis"""
        return f"""Provide a detailed analysis of spending in the {category} category:
- Total amount spent and percentage of overall expenses
- Comparison to recommended budget allocation
- Specific recommendations to optimize spending in this area
- Practical tips to reduce costs while maintaining quality of life"""

    @staticmethod
    def get_cashflow_prompt():
        """Get prompt for cashflow analysis"""
        return """Analyze the cashflow patterns:
- Monthly income and expense trends
- Identify months with surplus or deficit
- Predict potential cashflow issues
- Suggest strategies to maintain positive cashflow"""

    @staticmethod
    def get_financial_goals_prompt():
        """Get prompt for financial goals"""
        return """Based on the current financial situation, help set realistic financial goals:
- Short-term goals (3-6 months)
- Medium-term goals (1-2 years)
- Long-term goals (5+ years)
- Actionable steps to achieve each goal"""

    @staticmethod
    def get_budget_planner_analysis_prompt():
        """Get prompt for budget planner analysis"""
        return """Based on the financial data and budget allocations provided, analyze:
- How well the user is adhering to their budget
- Which categories are over or under budget
- Specific recommendations to stay on track
- Adjustments needed to make the budget more realistic
- Savings opportunities based on current vs budgeted spending"""

    @staticmethod
    def get_savings_goal_prompt():
        """Get prompt for savings goal recommendations"""
        return """Based on the current financial situation and income, provide:
- Realistic monthly savings target
- Timeframe to reach specific savings milestones
- Specific categories where spending can be reduced to meet savings goals
- Emergency fund recommendations
- Strategies to automate savings"""

    @staticmethod
    def get_budget_optimization_prompt():
        """Get prompt for budget optimization"""
        return """Analyze the current budget allocation and suggest optimizations:
- Are the budget percentages realistic based on spending patterns?
- Which categories need adjustment?
- How to balance needs vs wants
- Recommended changes to improve financial health
- Industry standard budget allocations vs current budget"""

import { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
    Area, 
    AreaChart, 
    ResponsiveContainer, 
    Tooltip, 
    XAxis, 
    YAxis, 
    CartesianGrid,
    PieChart,
    Pie,
    Cell,
    Legend
} from 'recharts';
import { ArrowUpRight, ArrowDownRight, DollarSign, Wallet, PiggyBank } from 'lucide-react';

// --- Types ---
interface Summary {
  total_balance: number;
  monthly_spending: number;
  savings_rate: number;
  currency: string;
}

interface CategoryData {
  name: string;
  value: number;
}

interface TrendData {
  date: string;
  amount: number;
}

interface Transaction {
  id: number;
  merchant: string;
  amount: number;
  date: string;
  category: string;
  type: string;
}

// --- Components ---

const SummaryCard = ({ title, value, subtext, icon: Icon, trend }: any) => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <Icon className="h-4 w-4 text-muted-foreground" />
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      <p className="text-xs text-muted-foreground mt-1 flex items-center">
        {trend === 'up' && <ArrowUpRight className="text-emerald-500 mr-1 h-4 w-4" />}
        {trend === 'down' && <ArrowDownRight className="text-rose-500 mr-1 h-4 w-4" />}
        {subtext}
      </p>
    </CardContent>
  </Card>
);

const COLORS = ['#0ea5e9', '#22c55e', '#eab308', '#f97316', '#ef4444', '#8b5cf6', '#ec4899'];

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [categories, setCategories] = useState<CategoryData[]>([]);
  const [trend, setTrend] = useState<TrendData[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sumRes, catRes, trendRes, txRes] = await Promise.all([
          axios.get('http://localhost:8000/api/dashboard/summary'),
          axios.get('http://localhost:8000/api/dashboard/categories'),
          axios.get('http://localhost:8000/api/dashboard/trend'),
          axios.get('http://localhost:8000/api/transactions?limit=5')
        ]);

        setSummary(sumRes.data);
        setCategories(catRes.data);
        setTrend(trendRes.data);
        setTransactions(txRes.data);
      } catch (error) {
        console.error("Failed to fetch dashboard data", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="p-8 flex items-center justify-center text-muted-foreground">Loading dashboard...</div>;
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Financial Overview</h2>
        <p className="text-muted-foreground">Welcome back! Here's what's happening with your money.</p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard 
          title="Total Balance" 
          value={`$${summary?.total_balance.toLocaleString()}`}
          subtext="Available funds"
          icon={Wallet}
        />
        <SummaryCard 
          title="Monthly Spending" 
          value={`$${summary?.monthly_spending.toLocaleString()}`}
          subtext="Total debit transactions this month"
          icon={DollarSign}
          trend="up" // Logic could be dynamic based on prev month
        />
        <SummaryCard 
          title="Savings Rate" 
          value={`${summary?.savings_rate}%`}
          subtext="of monthly income saved"
          icon={PiggyBank}
          trend={summary?.savings_rate && summary.savings_rate > 20 ? 'up' : 'down'}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        
        {/* Spending Trend Chart */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Spending Trend</CardTitle>
            <CardDescription>Daily spending over the last 30 days</CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend}>
                  <defs>
                    <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis 
                    dataKey="date" 
                    stroke="#888888" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false}
                    minTickGap={30}
                  />
                  <YAxis 
                    stroke="#888888" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false}
                    tickFormatter={(value) => `$${value}`}
                  />
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }}
                    itemStyle={{ color: '#0ea5e9' }}
                    formatter={(value: any) => [`$${Number(value).toFixed(2)}`, 'Spent']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="amount" 
                    stroke="#0ea5e9" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorAmount)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Category Breakdown */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Spending by Category</CardTitle>
            <CardDescription>Where your money went this month</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] flex items-center justify-center">
              {categories.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categories}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {categories.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                         contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }}
                         formatter={(value: any) => `$${Number(value).toFixed(2)}`}
                      />
                      <Legend verticalAlign="bottom" height={36}/>
                    </PieChart>
                  </ResponsiveContainer>
              ) : (
                  <div className="text-muted-foreground text-sm">No categorical data available</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Transactions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
          <CardDescription>Your latest financial activity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {transactions.map((t) => (
              <div key={t.id} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
                <div className="flex flex-col">
                  <span className="font-medium">{t.merchant}</span>
                  <span className="text-xs text-muted-foreground">{new Date(t.date).toLocaleDateString()} • {t.category}</span>
                </div>
                <div className={`font-bold ${t.type === 'credit' ? 'text-emerald-500' : ''}`}>
                  {t.type === 'credit' ? '+' : '-'}${t.amount.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
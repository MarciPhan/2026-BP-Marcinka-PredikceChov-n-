from typing import Dict, Any, List
import random
from datetime import datetime, timedelta

def get_demo_stats(start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Generate realistic mock data for the demo dashboard.
    Returns a unified dictionary containing all necessary stats keys.
    """
    
    # 1. Date Handling
    if start_date and end_date and start_date.strip() and end_date.strip():
        try:
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
            e_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except:
            e_dt = datetime.now()
            s_dt = e_dt - timedelta(days=30)
    else:
        e_dt = datetime.now()
        s_dt = e_dt - timedelta(days=30)
        
    date_list_dt = []
    curr = s_dt
    while curr <= e_dt:
        date_list_dt.append(curr)
        curr += timedelta(days=1)
    
    date_list_str = [d.strftime("%Y-%m-%d") for d in date_list_dt]
    days_count = len(date_list_str)

    # 2. Member Stats (Member Count, Joins, Leaves)
    total_members = 1250
    joins = []
    leaves = []
    totals = []
    
    # Generate history backwards from current total
    current_total = total_members
    
    # Reverse loop to calculate past totals
    temp_joins = []
    temp_leaves = []
    
    for _ in range(days_count):
        # Random daily variation
        j = random.randint(2, 15)
        l = random.randint(0, 8)
        
        # Sometimes spikes
        if random.random() > 0.9: j += 20
        
        temp_joins.append(j)
        temp_leaves.append(l)
        
    # Replay forward to get proper totals
    # We want the END of the series to be 1250.
    # So we need to work backwards from 1250
    
    runs = 1250
    totals_rev = []
    for j, l in zip(reversed(temp_joins), reversed(temp_leaves)):
        totals_rev.append(runs)
        runs = runs - (j - l)
        
    totals = list(reversed(totals_rev))
    joins = temp_joins
    leaves = temp_leaves

    # 3. Activity Stats (DAU/MAU)
    dau_data = []
    mau_data = []
    
    for _ in range(days_count):
        d = random.randint(200, 400)
        # Weekend dip
        if random.random() > 0.8: d = int(d * 0.7)
        dau_data.append(d)
        
        m = d * random.uniform(2.5, 3.5) # simple correlation
        mau_data.append(int(m))

    avg_dau = sum(dau_data) / len(dau_data) if dau_data else 0
    
    # 4. Hourly Activity (Heatmap & Bar Chart)
    hourly_activity = [0] * 24
    heatmap_data = [[0 for _ in range(24)] for _ in range(7)]
    
    # Simulate realistic activity curve
    activity_curve = [
        20, 10, 5, 2, 5, 15, 50, 120, 250, 400, 450, 480, 
        500, 520, 550, 600, 700, 800, 900, 950, 850, 600, 400, 150
    ]
    
    for h in range(24):
        base = activity_curve[h]
        hourly_activity[h] = base + random.randint(-20, 50)
        
        # Distribute to weekdays
        for w in range(7):
            val = int(base / 7) + random.randint(0, 50)
            if w >= 5: val = int(val * 1.5) # More activity on weekends
            heatmap_data[w][h] = val

    # 5. Message Length Distribution
    msglen_labels = ["0", "1-10", "11-50", "51-100", "101-200", "201+"]
    msglen_data = [50, 4500, 3200, 1500, 400, 100]

    # 6. Deep Stats (Leaderboard, etc.)
    active_staff_count = 15
    top_action = "Unbany"
    total_hours_30d = 1450.5
    
    leaderboard = [
        {"rank": 1, "name": "AdminMaster", "avatar": None, "action_count": 150, "weighted_h": 45.2, "role_names": ["Admin", "Mod"]},
        {"rank": 2, "name": "ModSarah", "avatar": None, "action_count": 120, "weighted_h": 38.5, "role_names": ["Mod"]},
        {"rank": 3, "name": "HelperJoe", "avatar": None, "action_count": 85, "weighted_h": 22.1, "role_names": ["Helper"]},
        {"rank": 4, "name": "BotDev", "avatar": None, "action_count": 40, "weighted_h": 15.0, "role_names": ["Dev"]},
        {"rank": 5, "name": "CommunityMgr", "avatar": None, "action_count": 25, "weighted_h": 40.0, "role_names": ["Manager"]}
    ]
    
    # Stickiness
    dau_wau_ratio = [random.uniform(15, 25) for _ in range(days_count)]
    dau_mau_ratio = [random.uniform(5, 12) for _ in range(days_count)]
    wau_data = [d * 3 for d in dau_data]
    
    # Weekly Radar
    weekly_counts = [sum(row) for row in heatmap_data]

    # Summary Card Data
    summary_stats = {
        "discord": {
            "users": totals[-1],
            "msgs": sum(hourly_activity) * days_count, # approx
            "dau": dau_data[-1],
            "mau": mau_data[-1],
            "wau": wau_data[-1]
        },
        "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    churn_rate = round((sum(leaves) / max(1, totals[-1])) * 100, 2)
    
    # 7. Analytics Tools Data
    trends = {
        "growth_7d": 12.5,
        "growth_30d": 45.2,
        "avg_dau": int(avg_dau),
        "prediction": int(avg_dau * 1.15)
    }
    
    engagement = {
        "score": 82,
        "msg_activity": 78,
        "voice_activity": 85,
        "retention": 83
    }
    
    security_score_data = {
        "overall_score": 88,
        "rating": "Vynikající",
        "rating_color": "#10B981",
        "mod_ratio_score": 95,
        "security_settings_score": 80,
        "engagement_score": 85,
        "moderation_score": 92
    }
    
    insights = [
        {"text": "✅ **Silný tým**: Skvělý poměr moderátorů – rychlá reakce zaručena."},
        {"text": "⚠️ **Slabé ověření**: Pouze e-mail. Zvažte vyšší úroveň."},
        {"text": "📈 **Vysoké zapojení**: 25.4% aktivních – výborné!"},
        {"text": "💡 **Interakce tip**: Přidejte ankety/hlasování pro více konverzací."}
    ]

    # Construct the final unified dictionary expected by the template
    return {
        "member_stats": {
            "labels": date_list_str,
            "total": totals,
            "joins": joins,
            "leaves": leaves
        },
        "activity_stats": {
            "dau_labels": date_list_str,
            "dau_data": dau_data,
            "mau_data": mau_data,
            "avg_dau": int(avg_dau)
        },
        "deep_stats": {
            "weekly_labels": ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"],
            "weekly_data": weekly_counts,
            "leaderboard": leaderboard,
            "active_staff_count": active_staff_count,
            "top_action": top_action,
            "total_hours_30d": total_hours_30d,
            "avg_msg_len": 42.5,
            "reply_ratio": 24.3,
            "peak_day": "Sobota",
            "retention_labels": date_list_str,
            "dau_mau_ratio": dau_mau_ratio,
            "dau_wau_ratio": dau_wau_ratio,
            "wau_data": wau_data
        },
        "redis_stats": {
            "hourly_activity": hourly_activity,
            "hourly_labels": [f"{h}:00" for h in range(24)],
            "msglen_labels": msglen_labels,
            "msglen_data": msglen_data,
            "heatmap_data": heatmap_data,
            "heatmap_max": max(max(row) for row in heatmap_data),
            "peak_hour": "20:00",
            "peak_day": "Sobota",
            "peak_messages": 950,
            "quiet_period": "03:00-05:00"
        },
        "stats": summary_stats,
        "realtime_active": 142,
        "churn_rate": churn_rate,
        "roles": [(1, "Admin"), (2, "Moderator"), (3, "Member")],
        "user_role": "admin",
        "start_date": start_date or date_list_str[0],
        "end_date": end_date or date_list_str[-1],
        "guild_id": "demo-guild",
        "total_members": totals[-1],
        "avg_dau": int(avg_dau),
        "avg_msg_len": 42.5,
        "reply_ratio": 24.3,
        "peak_day": "Sobota",
        # Charts Keys
        "dau_labels": date_list_str,
        "dau_data": dau_data,
        "labels": date_list_str,
        "joins_data": joins,
        "leaves_data": leaves,
        "total_data": totals,
        "hourly_labels": [f"{h}:00" for h in range(24)],
        "hourly_activity": hourly_activity,
        "retention_labels": date_list_str,
        "daily_labels": date_list_str,
        "daily_hours": [random.randint(5, 15) for _ in range(days_count)],
        "dau_mau_ratio": dau_mau_ratio,
        "dau_wau_ratio": dau_wau_ratio,
        "msglen_labels": msglen_labels,
        "msglen_data": msglen_data,
        "weekly_labels": ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"],
        "weekly_data": weekly_counts,
        # Analytics Tools
        "trends": trends,
        "engagement": engagement,
        "insights": insights,
        "security_score_data": security_score_data
    }

def get_demo_predictions_data() -> Dict[str, Any]:
    """Mock data for /api/predictions-data."""
    now = datetime.now()
    history_dates = [(now - timedelta(days=30*i)).strftime("%Y-%m") for i in range(12)][::-1]
    history_members = [1000 + i*20 + random.randint(-5, 5) for i in range(12)]
    
    forecast_dates = [(now + timedelta(days=30*i)).strftime("%Y-%m") for i in range(1, 7)]
    forecast_members = [history_members[-1] + i*25 for i in range(1, 7)]
    
    cz_days = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]
    forecast_day_labels = [(now + timedelta(days=i)).strftime("%a") for i in range(1, 8)] # Simplified
    forecast_day_labels = ["Út", "St", "Čt", "Pá", "So", "Ne", "Po"] # Hardcoded for predictability
    forecast_activity = [random.randint(800, 1200) for _ in range(7)]
    
    daus = [random.randint(280, 350) for _ in range(30)]
    dau_forecast = [random.randint(320, 360) for _ in range(7)]
    
    return {
        "history": {
            "dates": history_dates,
            "members": history_members,
            "joins": [random.randint(30, 60) for _ in range(12)],
            "leaves": [random.randint(10, 30) for _ in range(12)]
        },
        "forecast": {
            "dates": forecast_dates,
            "members": forecast_members,
            "days": forecast_day_labels,
            "activity": forecast_activity
        },
        "dau": {
            "history": daus,
            "history_labels": [(now - timedelta(days=29-i)).strftime("%Y-%m-%d") for i in range(30)],
            "forecast": dau_forecast,
            "forecast_labels": [(now + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 8)],
            "avg": sum(daus)//30,
            "trend": "up"
        },
        "mau": {
            "current": 1250,
            "forecast": [1250, 1280, 1310, 1345],
            "dau_mau_ratio": 24.5
        },
        "predictions": {
            "members_30d": 1280,
            "members_growth_pct": 2.4,
            "expected_msgs_tomorrow": 950,
            "expected_dau": 340,
            "avg_dau": 315,
            "churn_risk": 5,
            "avg_monthly_growth": 30.5,
            "current_members": 1250
        },
        "channels": [
            {"name": "general", "count": 450},
            {"name": "pokec", "count": 300},
            {"name": "hry", "count": 120},
            {"name": "bot-spam", "count": 80}
        ]
    }

def get_demo_logs() -> List[str]:
    """Mock live logs for demo mode."""
    actions = ["MESSAGE_CREATE", "VOICE_STATE_UPDATE", "MEMBER_JOIN", "MEMBER_LEAVE", "COMMAND_USED"]
    users = ["AdminMaster", "ModSarah", "HelperJoe", "User123", "DemoGuest"]
    channels = ["general", "pokec", "hry", "staff-lounge"]
    
    logs = []
    now = datetime.now()
    for i in range(20):
        time_str = (now - timedelta(seconds=i*30)).strftime("%H:%M:%S")
        action = random.choice(actions)
        user = random.choice(users)
        channel = random.choice(channels)
        
        if action == "MESSAGE_CREATE":
            msg = f"[{time_str}] {user}: sent message in #{channel}"
        elif action == "VOICE_STATE_UPDATE":
            msg = f"[{time_str}] {user}: joined voice channel 'General VC'"
        elif action == "COMMAND_USED":
            msg = f"[{time_str}] {user}: used command /stats"
        else:
            msg = f"[{time_str}] {user}: {action.lower().replace('_', ' ')}"
        logs.append(msg)
    return logs

def get_demo_user_activity(uid: int) -> Dict[str, Any]:
    """Mock activity data for a specific user."""
    days = 30
    now = datetime.now()
    labels = [(now - timedelta(days=i)).strftime("%m-%d") for i in range(days)][::-1]
    values = [random.uniform(0.5, 4.0) for _ in range(days)]
    
    return {
        "user_info": {
            "name": f"Demo User {uid}",
            "avatar": None,
            "roles": ["Moderator", "Active Member"]
        },
        "days": labels,
        "values": values,
        "summary": {
            "total_h": round(sum(values), 1),
            "chat_h": round(sum(values) * 0.6, 1),
            "voice_h": round(sum(values) * 0.4, 1),
            "actions": random.randint(50, 200),
            "breakdown": {
                "Bans": random.randint(0, 5),
                "Kicks": random.randint(0, 10),
                "Timeouts": random.randint(5, 30),
                "Unbans": random.randint(0, 2),
                "Verifications": random.randint(10, 50),
                "Deleted Msgs": random.randint(20, 100),
                "Role Updates": random.randint(5, 20)
            }
        }
    }


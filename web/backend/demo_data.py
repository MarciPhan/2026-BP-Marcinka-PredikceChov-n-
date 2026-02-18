from typing import Dict, Any, List
import random
from datetime import datetime, timedelta

def get_demo_stats(start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Generate realistic mock data for the demo dashboard.
    Returns a unified dictionary containing all necessary stats keys.
    """
    
    # 1. Date Handling
    if start_date and end_date:
        s_dt = datetime.strptime(start_date, "%Y-%m-%d")
        e_dt = datetime.strptime(end_date, "%Y-%m-%d")
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
        {"rank": 1, "username": "AdminMaster", "avatar": None, "action_count": 150, "weighted_h": 45.2, "role_names": ["Admin", "Mod"]},
        {"rank": 2, "username": "ModSarah", "avatar": None, "action_count": 120, "weighted_h": 38.5, "role_names": ["Mod"]},
        {"rank": 3, "username": "HelperJoe", "avatar": None, "action_count": 85, "weighted_h": 22.1, "role_names": ["Helper"]},
        {"rank": 4, "username": "BotDev", "avatar": None, "action_count": 40, "weighted_h": 15.0, "role_names": ["Dev"]},
        {"rank": 5, "username": "CommunityMgr", "avatar": None, "action_count": 25, "weighted_h": 40.0, "role_names": ["Manager"]}
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
            "avg_dau": round(avg_dau, 1)
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
        "avg_dau": round(avg_dau, 1),
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
        "dau_mau_ratio": dau_mau_ratio,
        "dau_wau_ratio": dau_wau_ratio,
        "msglen_labels": msglen_labels,
        "msglen_data": msglen_data,
        "weekly_labels": ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"],
        "weekly_data": weekly_counts
    }

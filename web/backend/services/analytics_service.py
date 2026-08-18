from typing import Dict, Any, List
from datetime import datetime, timedelta
import redis.asyncio as redis
import numpy as np

# Imports from data layer
# Removed direct repo import
# 



from .base import BaseAnalyticsService
from ..repositories.base import BaseRepository

class DefaultAnalyticsService(BaseAnalyticsService):
    def __init__(self, repo: BaseRepository):
        self.repo = repo

    async def get_trend_analysis(self, guild_id: int) -> Dict[str, Any]:
        """Calculate growth trends and predictions."""
        try:
            stats = await self.repo.get_activity_stats(guild_id, days=30)
            dau_data = stats.get("dau_data", [])
            
            dau_7d_vals = dau_data[-7:] if len(dau_data) >= 7 else dau_data
            dau_30d_vals = dau_data
            
            start_7 = dau_7d_vals[0] if dau_7d_vals else 0
            current_7 = dau_7d_vals[-1] if dau_7d_vals else 0
            growth_7d = ((current_7 - start_7) / max(1, start_7)) * 100
            
            start_30 = dau_30d_vals[0] if dau_30d_vals else 0
            current_30 = dau_30d_vals[-1] if dau_30d_vals else 0
            growth_30d = ((current_30 - start_30) / max(1, start_30)) * 100
            
            avg_dau = sum(dau_30d_vals) / max(1, len(dau_30d_vals))
            
            prediction = int(avg_dau * (1 + (growth_30d / 100)))
            
            return {
                "growth_7d": round(growth_7d, 1),
                "growth_30d": round(growth_30d, 1),
                "avg_dau": int(avg_dau),
                "prediction": prediction
            }
        except Exception as e:
            print(f"Trend error: {e}")
            return {"growth_7d": 0, "growth_30d": 0, "avg_dau": 0, "prediction": 0}
        finally:
            pass


    async def get_engagement_score(self, guild_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Calculate engagement score based on messages, voice, and retention."""
        r = await self.repo.get_client()
        try:
            
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                except:
                    start_dt = datetime.now() - timedelta(days=30)
                    end_dt = datetime.now()
            else:
                 start_dt = datetime.now() - timedelta(days=30)
                 end_dt = datetime.now()
            
            days_diff = (end_dt - start_dt).days + 1
            if days_diff < 1: days_diff = 1
            
            
            tm_str = await r.get(f"stats:total_members:{guild_id}")
            total_members = int(tm_str) if tm_str else 100
            
            dau_sum = 0
            current_day = start_dt
            while current_day <= end_dt:
                d_str = current_day.strftime("%Y%m%d")
                dau_sum += await r.pfcount(f"hll:dau:{guild_id}:{d_str}")
                current_day += timedelta(days=1)
            
            avg_dau = dau_sum / days_diff
            
            
            msg_participation_rate = (avg_dau / max(1, total_members))
            msg_score = min(100, (msg_participation_rate / 0.25) * 100)
            
            
            ts_start = start_dt.timestamp()
            ts_end = end_dt.replace(hour=23, minute=59, second=59).timestamp()
            
            total_voice_seconds = 0
            
            async for key in r.scan_iter(f"events:voice:{guild_id}:*"):
                events = await r.zrangebyscore(key, ts_start, ts_end)
                for evt_json in events:
                    try:
                        data = json.loads(evt_json)
                        total_voice_seconds += data.get("duration", 0)
                    except: pass
            
            
            hours_per_dau = (total_voice_seconds / days_diff / 3600) / max(1, avg_dau)
            voice_score = min(100, (hours_per_dau / 0.5) * 100)
            
            
            
            
            keys = []
            curr = start_dt
            while curr <= end_dt:
                 keys.append(f"hll:dau:{guild_id}:{curr.strftime('%Y%m%d')}")
                 curr += timedelta(days=1)
            
            period_unique = 0
            if keys:
                 
                 
                 
                 period_unique = await r.pfcount(*keys)
                 
            
            
            stickiness = (avg_dau / max(1, period_unique)) if period_unique > 0 else 0
            
            
            retention_score = min(100, (stickiness / 0.30) * 100)
            
            overall_score = int((msg_score * 0.4) + (voice_score * 0.3) + (retention_score * 0.3))
            
            return {
                "score": overall_score,
                "msg_activity": int(msg_score),
                "voice_activity": int(voice_score),
                "retention": int(retention_score),
                "debug_avg_dau": avg_dau,
                "debug_voice_hours": total_voice_seconds / 3600,
                "debug_unique": period_unique
            }
        except Exception as e:
             print(f"Engagement error: {e}")
             return {"score": 0, "msg_activity": 0, "voice_activity": 0, "retention": 0}
        finally:
            pass


    async def get_security_score(self, guild_id: int, days: int = 7) -> Dict[str, Any]:
        """
        Calculate security score based on multiple factors:
        - Moderator ratio (users per mod)
        - Server security settings (verification level, etc.)
        - User engagement/comfort (DAU, Reply Ratio, Voice - Last X Days)
        - Moderation health (active moderation)
        """
        r = await self.repo.get_client()
        try:
            
            
            weights = {"mod_ratio": 25, "security": 25, "engagement": 25, "moderation": 25}
            stored_weights = await r.hgetall("config:security_weights")
            if stored_weights:
                for k, v in stored_weights.items():
                    weights[k] = int(v)
            
            
            ideals = {
                "mod_ratio_min": 50, "mod_ratio_max": 100,
                "dau_percent": 25, 
                "mod_actions_min": 1, "mod_actions_max": 5,
                "verification_level": 2
            }
            stored_ideals = await r.hgetall("config:security_ideals")
            if stored_ideals:
                for k, v in stored_ideals.items():
                    ideals[k] = float(v) if '.' in str(v) else int(v)
            
            
            total_members_str = await r.get(f"presence:total:{guild_id}")
            if not total_members_str:
                total_members_str = await r.get(f"stats:total_members:{guild_id}")
            total_members = int(total_members_str) if total_members_str else 100
            
            mod_count_str = await r.get(f"stats:mod_count:{guild_id}")
            mod_count = int(mod_count_str) if mod_count_str else max(1, total_members // 100)
            
            users_per_mod = total_members / max(1, mod_count)
            ideal_min, ideal_max = ideals["mod_ratio_min"], ideals["mod_ratio_max"]
            
            if ideal_min <= users_per_mod <= ideal_max:
                mod_ratio_score = 100
            elif users_per_mod < ideal_min:
                mod_ratio_score = max(60, 100 - ((ideal_min - users_per_mod) / ideal_min) * 40)
            else:
                over_ratio = (users_per_mod - ideal_max) / ideal_max
                mod_ratio_score = max(0, 100 - over_ratio * 100)
            
            
            verification_level = int(await r.get(f"guild:verification_level:{guild_id}") or 2)
            verification_score = min(60, (verification_level / max(1, ideals["verification_level"])) * 60)
            explicit_score = (int(await r.get(f"guild:explicit_filter:{guild_id}") or 1) / 2) * 20
            mfa_score = 20 if int(await r.get(f"guild:mfa_level:{guild_id}") or 0) else 0
            
            security_settings_score = min(100, verification_score + explicit_score + mfa_score)
            
            
            now = datetime.now()
            start_ts = (now - timedelta(days=days)).timestamp()
            
            
            dau_sum = 0
            for i in range(days):
                d_str = (now - timedelta(days=i)).strftime("%Y%m%d")
                dau_sum += await r.pfcount(f"hll:dau:{guild_id}:{d_str}")
            avg_dau = dau_sum / days
            
            participation_rate = (avg_dau / max(1, total_members)) * 100
            participation_score = min(40, (participation_rate / ideals["dau_percent"]) * 40)
            
            
            
            
            
            
            total_msgs = 0
            total_replies = 0
            async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
                
                
                events = await r.zrangebyscore(key, start_ts, "+inf")
                for evt_json in events:
                    try:
                        data = json.loads(evt_json)
                        total_msgs += 1
                        if data.get("reply"): total_replies += 1
                    except: pass
            
            measured_reply_ratio = (total_replies / max(1, total_msgs)) * 100
            reply_score = min(30, (measured_reply_ratio / 20) * 30) 
            
            
            total_voice_seconds = 0
            async for key in r.scan_iter(f"events:voice:{guild_id}:*"):
                events = await r.zrangebyscore(key, start_ts, "+inf")
                for evt_json in events:
                    try:
                        data = json.loads(evt_json)
                        total_voice_seconds += data.get("duration", 0)
                    except: pass
                    
            
            
            
            hours_per_dau = (total_voice_seconds / days / 3600) / max(1, avg_dau)
            
            voice_score = min(30, (hours_per_dau / 0.5) * 30)

            engagement_score = int(participation_score + reply_score + voice_score)
            
            
            
            mod_actions = int(await r.get(f"stats:mod_actions_30d:{guild_id}") or (total_members // 50))
            
            actions_per_100_users = (mod_actions / max(1, total_members)) * 100
            ideal_actions_min = ideals["mod_actions_min"]
            ideal_actions_max = ideals["mod_actions_max"]
            
            if ideal_actions_min <= actions_per_100_users <= ideal_actions_max:
                moderation_score = 100
            elif actions_per_100_users < ideal_actions_min:
                
                moderation_score = 50
            elif actions_per_100_users <= ideal_actions_max * 2:
                
                moderation_score = 80
            else:
                
                moderation_score = max(20, 80 - (actions_per_100_users - ideal_actions_max * 2) * 5)
            
            
            overall_score = int(
                (mod_ratio_score * weights["mod_ratio"] / 100) +
                (security_settings_score * weights["security"] / 100) +
                (engagement_score * weights["engagement"] / 100) +
                (moderation_score * weights["moderation"] / 100)
            )
            
            
            if overall_score >= 80:
                rating = "Vynikající"
                rating_color = "#10B981"
            elif overall_score >= 60:
                rating = "Dobrý"
                rating_color = "#3B82F6"
            elif overall_score >= 40:
                rating = "Průměrný"
                rating_color = "#F59E0B"
            else:
                rating = "Nízký"
                rating_color = "#EF4444"

            

            
            curr_month = now.strftime("%Y-%m")
            month_leaves = int(await r.hget(f"stats:leaves:{guild_id}", curr_month) or 0)
            month_joins = int(await r.hget(f"stats:joins:{guild_id}", curr_month) or 0)
            churn_rate = (month_leaves / max(1, total_members)) * 100
            
            
            net_growth = month_joins - month_leaves
            growth_rate = (net_growth / max(1, total_members)) * 100
            
            
            mau_keys = [f"hll:dau:{guild_id}:{(now - timedelta(days=j)).strftime('%Y%m%d')}" for j in range(30)]
            mau = await r.pfcount(*mau_keys)
            stickiness = (avg_dau / max(1, mau)) * 100 if mau > 0 else 0

            explicit_filter = int(await r.get(f"guild:explicit_filter:{guild_id}") or 1)
            mfa_level = int(await r.get(f"guild:mfa_level:{guild_id}") or 0)
            
            
            avg_msg_length = 0
            try:
                msg_len_data = await r.get(f"stats:avg_msg_length:{guild_id}")
                avg_msg_length = float(msg_len_data) if msg_len_data else 0
            except:
                pass
            
            
            weekend_ratio = 1.0
            try:
                weekend_msgs = 0
                weekday_msgs = 0
                for i in range(14):  
                    d = now - timedelta(days=i)
                    d_str = d.strftime("%Y%m%d")
                    h_data = await r.hgetall(f"stats:hourly:{guild_id}:{d_str}")
                    day_sum = sum(int(float(v)) for v in h_data.values()) if h_data else 0
                    if d.weekday() >= 5:  
                        weekend_msgs += day_sum
                    else:
                        weekday_msgs += day_sum
                
                weekend_avg = weekend_msgs / 4 if weekend_msgs else 1
                weekday_avg = weekday_msgs / 10 if weekday_msgs else 1
                weekend_ratio = weekend_avg / max(1, weekday_avg)
            except:
                pass

            metrics = {
                "overall_score": overall_score,
                "mod_ratio": mod_ratio_score,
                "users_per_mod": users_per_mod,
                "mod_actions": mod_actions,
                "verification_level": verification_level,
                "mfa_level": mfa_level,
                "explicit_filter": explicit_filter,
                "participation_rate": participation_rate,
                "reply_ratio": measured_reply_ratio,
                "voice_hours_per_dau": hours_per_dau,
                "churn_rate": churn_rate,
                "stickiness": stickiness,
                
                "total_members": total_members,
                "avg_dau": avg_dau,
                "growth_rate": growth_rate,
                "engagement_score": engagement_score,
                "avg_msg_length": avg_msg_length,
                "weekend_ratio": weekend_ratio
            }

            
            return {
                "overall_score": overall_score,
                "rating": rating,
                "rating_color": rating_color,
                "weights": weights,
                "components": {
                    "mod_ratio": {
                        "score": int(mod_ratio_score),
                        "weight": int(weights["mod_ratio"]),
                        "label": "Poměr moderátorů",
                        "detail": f"{users_per_mod:.0f} uživatelů/mod"
                    },
                    "security": {
                        "score": int(security_settings_score),
                        "weight": int(weights["security"]),
                        "label": "Zabezpečení serveru",
                        "detail": f"Úroveň {verification_level}/4"
                    },
                    "engagement": {
                        "score": int(engagement_score),
                        "weight": int(weights["engagement"]),
                        "label": "Zapojení uživatelů",
                        "detail": f"{participation_rate:.2f}% aktivních" if participation_rate < 1 else f"{participation_rate:.1f}% aktivních"
                    },
                    "moderation": {
                        "score": int(moderation_score),
                        "weight": int(weights["moderation"]),
                        "label": "Zdraví moderace",
                        "detail": f"{mod_actions} akcí/měsíc"
                    }
                },
                "insights": generate_security_insights(metrics)
            }
        except Exception as e:
            print(f"Security score error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "overall_score": 0,
                "rating": "Neznámý",
                "rating_color": "#6B7280",
                "components": {},
                "insights": ["Nepodařilo se načíst postřehy."]
            }
        finally:
            pass


    async def get_insights(self, guild_id: int) -> List[Dict[str, str]]:
        """Generate smart insights based on stats."""
        insights = []
        
        try:
            trends = await get_trend_analysis(guild_id)
            score = await get_engagement_score(guild_id)
            
            
            if trends["growth_7d"] > 5:
                insights.append({"type": "positive", "text": "🚀 Silný týdenní růst! Počet aktivních uživatelů stoupá."})
            elif trends["growth_7d"] < -5:
                insights.append({"type": "negative", "text": "📉 Pozor, týdenní aktivita klesá. Zkuste uspořádat event."})
                
            
            if score["retention"] > 60:
                insights.append({"type": "positive", "text": "💎 Vysoká retence! Uživatelé se rádi vrací."})
            elif score["retention"] < 20:
                 insights.append({"type": "negative", "text": "⚠️ Nízká retence. Zaměřte se na udržení nových členů."})

            
            if score["voice_activity"] > 50:
                insights.append({"type": "positive", "text": "🗣️ Komunita je velmi upovídaná v hlasových kanálech!"})
            elif score["voice_activity"] < 10 and score["msg_activity"] > 50:
                insights.append({"type": "neutral", "text": "💬 Lidé píší, ale málo mluví. Zkuste vytvořit 'Chill' voice room."})
                
            
            cmd_stats = await self.repo.get_command_stats(guild_id, limit=1)
            if cmd_stats:
                top_cmd = cmd_stats[0]
                insights.append({"type": "neutral", "text": f"🤖 Nejoblíbenější příkaz je '/{top_cmd['name']}' ({top_cmd['count']}x)."})

            
            traffic = await self.repo.load_member_stats(guild_id)
            
            if traffic and "joins" in traffic and traffic["joins"]:
                 last_month_joins = traffic["joins"][-1] if len(traffic["joins"]) > 0 else 0
                 last_month_leaves = traffic["leaves"][-1] if len(traffic["leaves"]) > 0 else 0
                 if last_month_joins > last_month_leaves * 2:
                     insights.append({"type": "positive", "text": "📈 Skvělý nábor! Přichází 2x více lidí než odchází."})

            
            if trends["prediction"] > trends["avg_dau"] * 1.1:
                 insights.append({"type": "neutral", "text": f"🔮 Očekáváme růst na cca {trends['prediction']} denních uživatelů."})
                 
            
            if not insights:
                insights.append({"type": "neutral", "text": "Zatím nemám dost dat pro generování specifických postřehů."})
                
        except Exception as e:
             print(f"Insights error: {e}")
             insights.append({"type": "error", "text": "Chyba při generování postřehů."})
             
        return insights


    async def get_data_quality_score(self, guild_id: int) -> Dict[str, Any]:
        """
        Evaluate Data Quality Score (DQS) based on history length, number of events,
        and availability of different event types.
        """
        r = await self.repo.get_client()
        try:
            now = datetime.now()
            
            reasons = []
            score = 100
            
            # 1. History length
            first_seen = now.timestamp()
            total_msgs = 0
            
            async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
                msgs = await r.zrange(key, 0, 0, withscores=True)
                if msgs:
                    ts = float(msgs[0][1])
                    if ts < first_seen:
                        first_seen = ts
                total_msgs += await r.zcard(key)
                
            history_days = (now.timestamp() - first_seen) / 86400.0
            
            if history_days < 7:
                score -= 40
                reasons.append(f"Historie obsahuje pouze {max(1, int(history_days))} dny (doporučeno min. 7 dní).")
            elif history_days < 30:
                score -= 10
                reasons.append("Historie je kratší než 30 dní, dlouhodobé trendy mohou být nepřesné.")
                
            # 2. Number of events
            if total_msgs < 100:
                score -= 30
                reasons.append("Nedostatečný počet zpráv (méně než 100).")
                
            # 3. Required event types (moderation)
            mod_actions = int(await r.get(f"stats:mod_actions_30d:{guild_id}") or 0)
            if mod_actions == 0:
                score -= 15
                reasons.append("Chybí moderační události (index zátěže bude 0).")
                
            # 4. Voice events
            has_voice = False
            async for key in r.scan_iter(f"events:voice:{guild_id}:*"):
                if await r.zcard(key) > 0:
                    has_voice = True
                    break
            if not has_voice:
                score -= 10
                reasons.append("Chybí události z hlasových kanálů.")
                
            # 5. Connectors status (simulate Discourse)
            has_discourse = await r.hgetall(f"discourse:conf:{guild_id}")
            if not has_discourse:
                score -= 5
                reasons.append("Není připojeno fórum Discourse (zobrazují se pouze data z Discordu).")

            score = max(0, score)
            
            return {
                "score": score,
                "is_sufficient": score >= 50,
                "history_days": int(history_days),
                "total_events": total_msgs,
                "reasons": reasons
            }
        except Exception as e:
            print(f"DQS error: {e}")
            return {
                "score": 0,
                "is_sufficient": False,
                "history_days": 0,
                "total_events": 0,
                "reasons": ["Chyba při výpočtu kvality dat."]
            }

    async def get_action_weights(self) -> dict:
        """Fetch action weights from Redis or use defaults."""
        
        defaults = {
            "bans": 300, "kicks": 180, "timeouts": 180, "unbans": 120, 
            "verifications": 120, "msg_deleted": 60, "role_updates": 30,
            "chat_time": 1, "voice_time": 1,
            "session_base": 180, "char_weight": 1, "reply_weight": 60, "msg_weight": 0
        }
        
        try:
            r = await self.repo.get_client()
            if r:
                stored = await r.hgetall("config:action_weights")
            else:
                stored = None
                
            if stored:
                
                for k, v in stored.items():
                    if k in defaults:
                        defaults[k] = int(v)
        except Exception as e:
            print(f"Error fetching weights: {e}")
            
        return defaults


    async def get_health_research_data(self, guild_id: int) -> dict:
        import numpy as np
        from datetime import datetime, timedelta
        from shared.models import CommunityModels
        import json
        
        r = await self.repo.get_client()
        try:
            now = datetime.now()
            today_str = now.strftime("%Y%m%d")
            ts_now = now.timestamp()
            
            # 1. Total Members & DAU & Toxicity
            total_members_str = await r.get(f"presence:total:{guild_id}")
            total_members = int(total_members_str) if total_members_str else 0
            dau = await r.pfcount(f"hll:dau:{guild_id}:{today_str}")
            activity_rate = (dau / max(1, total_members))
            
            total_actions = 0
            async for key in r.scan_iter(f"events:action:{guild_id}:*"):
                total_actions += await r.zcard(key)
            total_msgs_str = await r.get(f"stats:total_msgs:{guild_id}")
            total_msgs = int(total_msgs_str) if total_msgs_str else 1
            toxicity_index = (total_actions / total_msgs)
            rec_mods = int(np.ceil((dau * (1 + toxicity_index * 10)) / 150 + 2))
            
            # 2. Extract User Timelines for ML Models
            user_activity = {} # uid -> list of active days (0 to 29, where 29 is today)
            user_first_seen = {}
            user_last_seen = {}
            
            ts_30d_ago = (now - timedelta(days=30)).timestamp()
            
            async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
                uid = key.split(":")[-1]
                msgs = await r.zrange(key, 0, -1, withscores=True)
                if not msgs: continue
                
                first_ts = float(msgs[0][1])
                last_ts = float(msgs[-1][1])
                user_first_seen[uid] = first_ts
                user_last_seen[uid] = last_ts
                
                # Map activity to last 30 days
                active_days = set()
                for msg_json, score in msgs:
                    ts = float(score)
                    if ts >= ts_30d_ago:
                        days_ago = (now - datetime.fromtimestamp(ts)).days
                        day_idx = 29 - days_ago
                        if 0 <= day_idx <= 29:
                            active_days.add(day_idx)
                user_activity[uid] = active_days

            # 3. Build Markov Transitions
            transitions = []
            current_distribution = [0, 0, 0, 0, 0] # New, Active, Passive, Inactive, Churned
            
            for uid, active_days in user_activity.items():
                prev_state = None
                join_date = datetime.fromtimestamp(user_first_seen.get(uid, ts_30d_ago))
                join_day_idx = 29 - (now - join_date).days
                
                for day_idx in range(max(0, join_day_idx), 30):
                    # Calculate days since last active relative to current simulated day
                    last_active_before_or_on = [d for d in active_days if d <= day_idx]
                    days_since = day_idx - last_active_before_or_on[-1] if last_active_before_or_on else (day_idx - join_day_idx)
                    
                    state = 4 # Churned
                    if days_since == 0 and day_idx == join_day_idx: state = 0 # New
                    elif days_since <= 2: state = 1 # Active
                    elif days_since <= 7: state = 2 # Passive
                    elif days_since <= 14: state = 3 # Inactive
                    
                    if prev_state is not None:
                        transitions.append((prev_state, state))
                    prev_state = state
                    
                    if day_idx == 29: # Today
                        current_distribution[state] += 1
                        
            # 4. Markov Prediction
            if transitions:
                matrix = CommunityModels.calculate_markov_matrix(transitions, num_states=5)
                # Normalize current distribution
                total_users = sum(current_distribution)
                if total_users > 0:
                    current_vec = np.array(current_distribution) / total_users
                    future_vec = CommunityModels.predict_future_states(current_vec, matrix, steps=7)
                    p_stay_active = future_vec[1] + future_vec[2] # Active + Passive
                    p_churn = future_vec[4] # Predicted Churned
                else:
                    p_stay_active = 0.6
                    p_churn = 0.05
            else:
                p_stay_active = 0.6 + (activity_rate * 0.5)
                p_churn = 0.05 + (toxicity_index * 2)
                
            # 5. Kaplan-Meier Survival Analysis
            durations = []
            event_observed = []
            
            for uid, first_ts in user_first_seen.items():
                last_ts = user_last_seen.get(uid, first_ts)
                days_active = (last_ts - first_ts) / 86400.0
                days_since_last = (ts_now - last_ts) / 86400.0
                
                is_churned = days_since_last > 14
                durations.append(int(max(1, days_active)))
                event_observed.append(is_churned)
                
            life_exp = 30.0
            half_life = 15.0
            curve = {}
            if durations:
                curve = CommunityModels.calculate_survival_rate(durations, event_observed)
                life_exp = CommunityModels.estimate_life_expectancy(curve)
                half_life = life_exp * 0.69 # Approximate
                
            # Převod stavů pro API
            dist_dict = {
                "new": current_distribution[0],
                "active": current_distribution[1],
                "passive": current_distribution[2],
                "inactive": current_distribution[3],
                "churned": current_distribution[4]
            }
            
            future_dist = {
                "new": future_vec[0] if 'future_vec' in locals() else 0,
                "active": future_vec[1] if 'future_vec' in locals() else 0,
                "passive": future_vec[2] if 'future_vec' in locals() else 0,
                "inactive": future_vec[3] if 'future_vec' in locals() else 0,
                "churned": future_vec[4] if 'future_vec' in locals() else 0
            }
                
            return {
                "success": True,
                "activity_rate_pct": round(activity_rate * 100, 1),
                "toxicity_index_pct": round(toxicity_index * 100, 2),
                "rec_mods": rec_mods,
                "retention_pct": round(p_stay_active * 100, 1),
                "churn_risk_pct": round(p_churn * 100, 1),
                "life_expectancy_days": round(life_exp, 1),
                "half_life_days": round(half_life, 1),
                "state_distribution": dist_dict,
                "predicted_distribution": future_dist,
                "survival_curve": curve
            }
        except Exception as e:
            print(f"Error computing health research data: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

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
            
            if not dau_data:
                return {
                    "available": False,
                    "reason": "no_activity_history",
                    "growth_7d": None,
                    "growth_30d": None,
                    "avg_dau": None,
                    "trend_projection": None,
                    "prediction": None,
                    "projection_method": None,
                    "validated_prediction": False
                }
                
            if len(dau_data) < 7:
                return {
                    "available": False,
                    "reason": "insufficient_history",
                    "growth_7d": None,
                    "growth_30d": None,
                    "avg_dau": None,
                    "trend_projection": None,
                    "prediction": None,
                    "projection_method": None,
                    "validated_prediction": False
                }
            
            dau_7d_vals = dau_data[-7:]
            dau_30d_vals = dau_data
            
            start_7 = dau_7d_vals[0]
            current_7 = dau_7d_vals[-1]
            growth_7d = ((current_7 - start_7) / start_7) * 100 if start_7 > 0 else 0
            
            start_30 = dau_30d_vals[0]
            current_30 = dau_30d_vals[-1]
            growth_30d = ((current_30 - start_30) / start_30) * 100 if start_30 > 0 else 0
            
            avg_dau = sum(dau_30d_vals) / len(dau_30d_vals)
            
            trend_projection = int(avg_dau * (1 + (growth_30d / 100)))
            
            return {
                "available": True,
                "reason": None,
                "growth_7d": round(growth_7d, 1),
                "growth_30d": round(growth_30d, 1),
                "avg_dau": int(avg_dau),
                "trend_projection": trend_projection,
                "prediction": trend_projection,
                "projection_method": "simple_extrapolation",
                "validated_prediction": False
            }
        except Exception as e:
            print(f"Trend error: {e}")
            return {
                "available": False,
                "reason": "calculation_error",
                "growth_7d": None,
                "growth_30d": None,
                "avg_dau": None,
                "trend_projection": None,
                "prediction": None
            }
        finally:
            pass


    async def get_engagement_score(self, guild_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Calculate Engagement Score using formula:
        S_eng = 100 * (w_u*U + w_m*M + w_r*R + w_v*V) / sum(w)
        Missing components are omitted from the denominator.
        All components U, M, R, V are normalized to 0-1.
        """
        r = await self.repo.get_client()
        try:
            import json
            
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
            
            ts_start = start_dt.timestamp()
            ts_end = end_dt.replace(hour=23, minute=59, second=59).timestamp()
            
            # Fetch config weights
            raw_weights = await r.hgetall(f"config:engagement_weights:{guild_id}")
            weights = {
                "u": float(raw_weights.get("u", 1.0)),
                "m": float(raw_weights.get("m", 1.0)),
                "r": float(raw_weights.get("r", 1.0)),
                "v": float(raw_weights.get("v", 1.0))
            }
            
            # 1. Users (U): DAU / Total Members (Normalized 0 to 25% max)
            tm_str = await r.get(f"stats:total_members:{guild_id}")
            total_members = int(tm_str) if tm_str is not None else None
            
            numerator = 0.0
            denominator = 0.0
            components = {}
            
            dau_sum = 0
            current_day = start_dt
            while current_day <= end_dt:
                d_str = current_day.strftime("%Y%m%d")
                dau_sum += await r.pfcount(f"hll:dau:{guild_id}:{d_str}")
                current_day += timedelta(days=1)
            
            avg_dau = dau_sum / days_diff
            
            if total_members is not None and total_members > 0:
                val_u = (avg_dau / total_members)
                norm_u = min(1.0, val_u / 0.25) # 25% participation is 1.0
                numerator += weights["u"] * norm_u
                denominator += weights["u"]
                components["users"] = {
                    "value": int(norm_u * 100),
                    "available": True,
                    "reason": None
                }
            else:
                components["users"] = {
                    "value": None,
                    "available": False,
                    "reason": "missing_member_count"
                }
            
            # 2. Messages (M) & 3. Reactions (R)
            total_msgs = 0
            total_reactions = 0
            has_message_data = False
            has_reaction_data = False
            
            async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
                events = await r.zrangebyscore(key, ts_start, ts_end)
                for evt_json in events:
                    has_message_data = True
                    try:
                        data = json.loads(evt_json)
                        total_msgs += 1
                        reactions = int(data.get("reaction_count", 0))
                        if reactions > 0 or "reaction_count" in data:
                            has_reaction_data = True
                        total_reactions += reactions
                    except: pass
            
            if has_message_data:
                val_m = total_msgs / max(1, avg_dau * days_diff) # Msgs per DAU
                norm_m = min(1.0, val_m / 5.0) # 5 messages per DAU is 1.0
                numerator += weights["m"] * norm_m
                denominator += weights["m"]
                components["messages"] = {
                    "value": int(norm_m * 100),
                    "available": True,
                    "reason": None
                }
            else:
                components["messages"] = {
                    "value": None,
                    "available": False,
                    "reason": "no_message_data"
                }
            
            if has_reaction_data:
                val_r = total_reactions / max(1, total_msgs) # Reactions per msg
                norm_r = min(1.0, val_r / 2.0) # 2 reactions per msg is 1.0
                numerator += weights["r"] * norm_r
                denominator += weights["r"]
                components["reactions"] = {
                    "value": int(norm_r * 100),
                    "available": True,
                    "reason": None
                }
            else:
                components["reactions"] = {
                    "value": None,
                    "available": False,
                    "reason": "no_reaction_data"
                }
            
            # 4. Voice (V)
            total_voice_seconds = 0
            has_voice_data = False
            
            async for key in r.scan_iter(f"events:voice:{guild_id}:*"):
                has_voice_data = True
                events = await r.zrangebyscore(key, ts_start, ts_end)
                for evt_json in events:
                    try:
                        data = json.loads(evt_json)
                        total_voice_seconds += data.get("duration", 0)
                    except: pass
            
            if has_voice_data:
                val_v = (total_voice_seconds / days_diff / 3600) / max(1, avg_dau) # Hours per DAU
                norm_v = min(1.0, val_v / 0.5) # 0.5 hours per DAU is 1.0
                numerator += weights["v"] * norm_v
                denominator += weights["v"]
                components["voice"] = {
                    "value": int(norm_v * 100),
                    "available": True,
                    "reason": None
                }
            else:
                components["voice"] = {
                    "value": None,
                    "available": False,
                    "reason": "voice_data_unavailable"
                }
                
            if denominator > 0:
                overall_score = int(100 * (numerator / denominator))
            else:
                return {
                    "score": None, 
                    "available": False, 
                    "reason": "no_components_available", 
                    "components": components
                }
            
            return {
                "available": True,
                "score": overall_score,
                "msg_activity": components["messages"]["value"] if components.get("messages", {}).get("available") else None,
                "voice_activity": components["voice"]["value"] if components.get("voice", {}).get("available") else None,
                "components": components,
                "debug_avg_dau": avg_dau,
                "debug_voice_hours": total_voice_seconds / 3600
            }
        except Exception as e:
             print(f"Engagement error: {e}")
             return {
                 "score": None,
                 "available": False,
                 "reason": "calculation_error",
                 "components": {}
             }
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
            total_members = int(total_members_str) if total_members_str is not None else None
            
            mod_count_str = await r.get(f"stats:mod_count:{guild_id}")
            mod_count = int(mod_count_str) if mod_count_str is not None else None
            
            available_components_list = []
            
            if total_members is not None and total_members > 0 and mod_count is not None and mod_count > 0:
                users_per_mod = total_members / mod_count
                ideal_min, ideal_max = ideals["mod_ratio_min"], ideals["mod_ratio_max"]
                
                if ideal_min <= users_per_mod <= ideal_max:
                    mod_ratio_score = 100
                elif users_per_mod < ideal_min:
                    mod_ratio_score = max(60, 100 - ((ideal_min - users_per_mod) / ideal_min) * 40)
                else:
                    over_ratio = (users_per_mod - ideal_max) / ideal_max
                    mod_ratio_score = max(0, 100 - over_ratio * 100)
                available_components_list.append((mod_ratio_score, weights["mod_ratio"], "mod_ratio"))
            else:
                users_per_mod = None
                mod_ratio_score = None
            
            ver_level_str = await r.get(f"guild:verification_level:{guild_id}")
            verification_level = int(ver_level_str) if ver_level_str is not None else None
            exp_filter_str = await r.get(f"guild:explicit_filter:{guild_id}")
            explicit_filter = int(exp_filter_str) if exp_filter_str is not None else None
            mfa_level_str = await r.get(f"guild:mfa_level:{guild_id}")
            mfa_level = int(mfa_level_str) if mfa_level_str is not None else None
            
            if verification_level is not None and explicit_filter is not None and mfa_level is not None:
                verification_score = min(60, (verification_level / max(1, ideals["verification_level"])) * 60)
                explicit_score = (explicit_filter / 2) * 20
                mfa_score = 20 if mfa_level else 0
                security_settings_score = min(100, verification_score + explicit_score + mfa_score)
                available_components_list.append((security_settings_score, weights["security"], "security"))
            else:
                security_settings_score = None
            
            now = datetime.now()
            start_ts = (now - timedelta(days=days)).timestamp()
            
            dau_sum = 0
            for i in range(days):
                d_str = (now - timedelta(days=i)).strftime("%Y%m%d")
                dau_sum += await r.pfcount(f"hll:dau:{guild_id}:{d_str}")
            avg_dau = dau_sum / days
            
            if total_members is not None and total_members > 0:
                participation_rate = (avg_dau / total_members) * 100
                participation_score = min(40, (participation_rate / ideals["dau_percent"]) * 40)
            else:
                participation_rate = None
                participation_score = None
            
            from web.backend.services.community_health_service import CommunityHealthService
            health_svc = CommunityHealthService(r)
            help_data = await health_svc.help_requests(guild_id, days=days, limit=1)
            
            answerable_posts = help_data.get("total", 0)
            answered_posts = help_data.get("answered", 0)
            
            if answerable_posts > 0:
                measured_reply_ratio = (answered_posts / answerable_posts) * 100
                reply_score = min(30.0, (measured_reply_ratio / 80.0) * 30.0)
            else:
                measured_reply_ratio = None
                reply_score = None
            
            total_voice_seconds = 0
            async for key in r.scan_iter(f"events:voice:{guild_id}:*"):
                events = await r.zrangebyscore(key, start_ts, "+inf")
                for evt_json in events:
                    try:
                        data = json.loads(evt_json)
                        total_voice_seconds += data.get("duration", 0)
                    except: pass
                    
            if total_voice_seconds > 0:
                hours_per_dau = (total_voice_seconds / days / 3600) / max(1, avg_dau)
                voice_score = min(30, (hours_per_dau / 0.5) * 30)
            else:
                hours_per_dau = 0
                voice_score = None

            eng_w = 0
            eng_s = 0
            if participation_score is not None:
                eng_w += 40
                eng_s += participation_score
            if reply_score is not None:
                eng_w += 30
                eng_s += reply_score
            if voice_score is not None:
                eng_w += 30
                eng_s += voice_score
                
            if eng_w > 0:
                engagement_score = int(eng_s * (100.0 / eng_w))
                available_components_list.append((engagement_score, weights["engagement"], "engagement"))
            else:
                engagement_score = None
            
            mod_actions_count = 0
            mod_keys_found = False
            async for key in r.scan_iter(f"events:action:{guild_id}:*"):
                mod_keys_found = True
                mod_actions_count += await r.zcard(key)
            mod_actions = mod_actions_count if mod_keys_found else None
            
            if mod_actions is not None and total_members is not None and total_members > 0:
                actions_per_100_users = (mod_actions / total_members) * 100
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
                available_components_list.append((moderation_score, weights["moderation"], "moderation"))
            else:
                actions_per_100_users = None
                moderation_score = None
            
            weight_sum = sum(weight for _, weight, _ in available_components_list)
            weighted_sum = sum(score * weight for score, weight, _ in available_components_list)
            
            if weight_sum > 0:
                overall_score = int(weighted_sum / weight_sum)
            else:
                overall_score = None
            
            if overall_score is not None:
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
            else:
                rating = "Neznámý"
                rating_color = "#6B7280"
            
            curr_month = now.strftime("%Y-%m")
            month_leaves = int(await r.hget(f"stats:leaves:{guild_id}", curr_month) or 0)
            month_joins = int(await r.hget(f"stats:joins:{guild_id}", curr_month) or 0)
            churn_rate = (month_leaves / max(1, total_members)) * 100 if total_members else 0
            
            net_growth = month_joins - month_leaves
            growth_rate = (net_growth / max(1, total_members)) * 100 if total_members else 0
            
            mau_keys = [f"hll:dau:{guild_id}:{(now - timedelta(days=j)).strftime('%Y%m%d')}" for j in range(30)]
            mau = await r.pfcount(*mau_keys)
            stickiness = (avg_dau / max(1, mau)) * 100 if mau > 0 else 0
            
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
            
            components_out = {}
            if mod_ratio_score is not None:
                components_out["mod_ratio"] = {
                    "score": int(mod_ratio_score),
                    "weight": int(weights["mod_ratio"]),
                    "label": "Poměr moderátorů",
                    "detail": f"{users_per_mod:.0f} uživatelů/mod"
                }
            if security_settings_score is not None:
                components_out["security"] = {
                    "score": int(security_settings_score),
                    "weight": int(weights["security"]),
                    "label": "Zabezpečení serveru",
                    "detail": f"Úroveň {verification_level}/4"
                }
            if engagement_score is not None:
                components_out["engagement"] = {
                    "score": int(engagement_score),
                    "weight": int(weights["engagement"]),
                    "label": "Zapojení uživatelů",
                    "detail": f"{participation_rate:.2f}% aktivních" if participation_rate and participation_rate < 1 else f"{participation_rate or 0:.1f}% aktivních"
                }
            if moderation_score is not None:
                components_out["moderation"] = {
                    "score": int(moderation_score),
                    "weight": int(weights["moderation"]),
                    "label": "Zdraví moderace",
                    "detail": f"{mod_actions} akcí/měsíc"
                }

            from web.backend.utils import generate_security_insights
            return {
                "overall_score": overall_score,
                "available": overall_score is not None,
                "rating": rating,
                "rating_color": rating_color,
                "weights": weights,
                "components": components_out,
                "insights": generate_security_insights(metrics)
            }
        except Exception as e:
            print(f"Security score error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "overall_score": None,
                "available": False,
                "reason": "calculation_error",
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
            trends = await self.get_trend_analysis(guild_id)
            score = await self.get_engagement_score(guild_id)
            
            
            if trends["growth_7d"] > 5:
                insights.append({"type": "positive", "text": "🚀 Silný týdenní růst! Počet aktivních uživatelů stoupá."})
            elif trends["growth_7d"] < -5:
                insights.append({"type": "negative", "text": "📉 Pozor, týdenní aktivita klesá. Zkuste uspořádat event."})
                
            
            user_component = score.get("components", {}).get("users")
            if user_component and user_component.get("available"):
                u_val = user_component.get("value", 0)
                if u_val > 60:
                    insights.append({"type": "positive", "text": "💎 Vysoký podíl aktivních členů v aktuálním období."})
                elif u_val < 20:
                     insights.append({"type": "negative", "text": "⚠️ Nízký podíl aktivních členů v aktuálním období."})

            
            if score.get("voice_activity") and score["voice_activity"] > 50:
                insights.append({"type": "positive", "text": "🗣️ Komunita je velmi upovídaná v hlasových kanálech!"})
            elif score.get("voice_activity") and score["voice_activity"] < 10 and score.get("msg_activity") and score["msg_activity"] > 50:
                insights.append({"type": "neutral", "text": "💬 Lidé píší, ale málo mluví. Zkuste vytvořit 'Chill' voice room."})
                
            
            from ..utils import get_command_stats
            cmd_stats = await get_command_stats(guild_id, limit=1)
            if cmd_stats:
                top_cmd = cmd_stats[0]
                insights.append({"type": "neutral", "text": f"🤖 Nejoblíbenější příkaz je '/{top_cmd['name']}' ({top_cmd['count']}x)."})

            
            traffic = await self.repo.load_member_stats(guild_id)
            
            if traffic and "joins" in traffic and traffic["joins"]:
                 last_month_joins = traffic["joins"][-1] if len(traffic["joins"]) > 0 else 0
                 last_month_leaves = traffic["leaves"][-1] if len(traffic["leaves"]) > 0 else 0
                 if last_month_joins > last_month_leaves * 2:
                     insights.append({"type": "positive", "text": "📈 Skvělý nábor! Přichází 2x více lidí než odchází."})

            
            if trends.get("prediction") and trends.get("avg_dau") and trends["prediction"] > trends["avg_dau"] * 1.1:
                 insights.append({"type": "neutral", "text": f"🔮 Jednoduchá extrapolace současného trendu odpovídá přibližně {trends['prediction']} denním aktivním uživatelům. Nejde o validovaný prediktivní model."})
                 
            
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
            mod_keys_found = False
            async for key in r.scan_iter(f"events:action:{guild_id}:*"):
                mod_keys_found = True
                break
            
            if not mod_keys_found:
                score -= 15
                reasons.append("Moderační data nejsou dostupná.")
                
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
                "score": None,
                "is_sufficient": False,
                "history_days": None,
                "total_events": None,
                "available": False,
                "reason": "calculation_error",
                "reasons": ["Chyba při výpočtu kvality dat."]
            }

    async def get_mii_weights(self) -> dict:
        """Fetch MII weights."""
        from shared.analytics_config import DEFAULT_MII_WEIGHTS
        return DEFAULT_MII_WEIGHTS

    async def get_action_weights(self, *args, **kwargs) -> dict:
        """Fetch action weights from Redis or use defaults."""
        
        from shared.analytics_config import DEFAULT_MII_WEIGHTS
        defaults = {
            "ban": DEFAULT_MII_WEIGHTS["ban"], 
            "kick": DEFAULT_MII_WEIGHTS["kick"], 
            "timeout": DEFAULT_MII_WEIGHTS["timeout"],
            "msg_delete": DEFAULT_MII_WEIGHTS["msg_delete"],
            "unbans": 120, "verifications": 120, "role_updates": 30,
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
        from shared.models import CommunityModels, UserState
        import json
        
        r = await self.repo.get_client()
        try:
            now = datetime.now()
            today_str = now.strftime("%Y%m%d")
            ts_now = now.timestamp()
            
            # 1. Total Members & DAU
            total_members_str = await r.get(f"presence:total:{guild_id}")
            total_members = int(total_members_str) if total_members_str is not None else None
            dau = await r.pfcount(f"hll:dau:{guild_id}:{today_str}")
            activity_rate = (dau / total_members) if total_members is not None and total_members > 0 else None
            
            # Moderation Intervention Index (MII)
            weights = await self.get_mii_weights()
            weighted_mod_actions = 0
            ts_30d_ago = (now - timedelta(days=30)).timestamp()
            
            async for key in r.scan_iter(f"events:action:{guild_id}:*"):
                events = await r.zrangebyscore(key, ts_30d_ago, "+inf")
                for evt_json in events:
                    try:
                        data = json.loads(evt_json)
                        action_type = data.get("type") or data.get("action") or "unknown"
                        if action_type in weights:
                            weighted_mod_actions += weights[action_type]
                        elif action_type.endswith("s") and action_type[:-1] in weights:
                            weighted_mod_actions += weights[action_type[:-1]]
                    except: pass
                    
            total_interactions_30d = 0
            async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
                msgs = await r.zrangebyscore(key, ts_30d_ago, "+inf")
                total_interactions_30d += len(msgs)
                for m_json in msgs:
                    try:
                        m_data = json.loads(m_json)
                        total_interactions_30d += int(m_data.get("reaction_count", 0))
                    except: pass
            
            if total_interactions_30d > 0:
                mii = weighted_mod_actions / total_interactions_30d
            else:
                # BP requirement: if N_interactions == 0, MII is unavailable, not zero
                mii = None
            
            # 2. Extract User Timelines for ML Models
            user_activity = {} # uid -> list of active days (0 to 29, where 29 is today)
            user_first_observed_activity = {}
            user_last_seen = {}
            
            ts_30d_ago = (now - timedelta(days=30)).timestamp()
            
            async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
                uid = key.split(":")[-1]
                # BP requirement: skip Discourse pseudo-user from Markov analysis
                if uid == "discourse":
                    continue
                first_msg = await r.zrange(key, 0, 0, withscores=True)
                if first_msg:
                    user_first_observed_activity[uid] = float(first_msg[0][1])
                else:
                    continue
                    
                msgs = await r.zrangebyscore(key, ts_30d_ago, "+inf", withscores=True)
                if not msgs: continue
                
                last_ts = float(msgs[-1][1])
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

            # 3. Build Markov Transitions (4 states)
            transitions = []
            current_distribution = [0, 0, 0, 0] # New, Active, Passive, Inactive
            
            basis_member_join = 0
            basis_first_observed = 0
            
            for uid, active_days in user_activity.items():
                prev_state = None
                
                join_ts_str = await r.hget(f"user:info:{uid}", "joined_at")
                if join_ts_str:
                    first_observed_ts = float(join_ts_str)
                    basis_member_join += 1
                else:
                    first_observed_ts = user_first_observed_activity.get(uid, ts_30d_ago)
                    basis_first_observed += 1

                first_observed_date = datetime.fromtimestamp(first_observed_ts)
                first_observed_day_idx = 29 - (now - first_observed_date).days
                
                for day_idx in range(max(0, first_observed_day_idx), 30):
                    last_active_before_or_on = [d for d in active_days if d <= day_idx]
                    days_since = day_idx - last_active_before_or_on[-1] if last_active_before_or_on else (day_idx - first_observed_day_idx)
                    
                    state = UserState.INACTIVE
                    if days_since == 0 and day_idx == first_observed_day_idx: state = UserState.NEW
                    elif days_since <= 2: state = UserState.ACTIVE
                    elif days_since <= 7: state = UserState.PASSIVE
                    else: state = UserState.INACTIVE
                    
                    if prev_state is not None:
                        transitions.append((prev_state.value, state.value))
                    prev_state = state
                    
                    if day_idx == 29: # Today
                        current_distribution[state.value] += 1
                        
            # 4. Markov Prediction
            p_stay_active = None
            p_inactive = None
            future_dist = None
            predicted_distribution_available = False
            predicted_distribution_reason = "insufficient_transitions"
            
            if basis_member_join > 0 and basis_first_observed > 0:
                global_new_state_basis = "mixed"
            elif basis_member_join > 0:
                global_new_state_basis = "member_join"
            else:
                global_new_state_basis = "first_observed_activity"

            if len(transitions) >= 5:
                matrix = CommunityModels.calculate_markov_matrix(transitions, num_states=4)
                total_users = sum(current_distribution)
                if total_users > 0:
                    current_vec = np.array(current_distribution) / total_users
                    future_vec = CommunityModels.predict_future_states(current_vec, matrix, steps=7)
                    if np.isclose(future_vec.sum(), 1.0):
                        p_stay_active = future_vec[UserState.ACTIVE.value] + future_vec[UserState.PASSIVE.value]
                        p_inactive = future_vec[UserState.INACTIVE.value]
                        future_dist = {
                            "new": future_vec[UserState.NEW.value],
                            "active": future_vec[UserState.ACTIVE.value],
                            "passive": future_vec[UserState.PASSIVE.value],
                            "inactive": future_vec[UserState.INACTIVE.value]
                        }
                        predicted_distribution_available = True
                        predicted_distribution_reason = None
                    else:
                        predicted_distribution_reason = "insufficient_transitions"
                
            from shared.config import settings
            ACTIVITY_INACTIVITY_THRESHOLD_DAYS = settings.activity_inactivity_threshold_days
            ACTIVITY_INACTIVITY_THRESHOLD_SECONDS = ACTIVITY_INACTIVITY_THRESHOLD_DAYS * 86400
            durations = []
            event_observed = []
            global_first_seen = ts_now
            
            async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
                msgs = await r.zrange(key, 0, -1, withscores=True)
                if not msgs: continue
                
                timestamps = [float(score) for _, score in msgs]
                observation_start = timestamps[0]
                if observation_start < global_first_seen:
                    global_first_seen = observation_start
                
                observation_end = ts_now
                has_event = False
                
                for i in range(len(timestamps) - 1):
                    prev_activity = timestamps[i]
                    next_activity = timestamps[i+1]
                    if next_activity - prev_activity > ACTIVITY_INACTIVITY_THRESHOLD_SECONDS:
                        event_time = prev_activity + ACTIVITY_INACTIVITY_THRESHOLD_SECONDS
                        durations.append((event_time - observation_start) / 86400.0)
                        event_observed.append(True)
                        has_event = True
                        break
                        
                if not has_event:
                    last_activity = timestamps[-1]
                    if observation_end - last_activity > ACTIVITY_INACTIVITY_THRESHOLD_SECONDS:
                        event_time = last_activity + ACTIVITY_INACTIVITY_THRESHOLD_SECONDS
                        durations.append((event_time - observation_start) / 86400.0)
                        event_observed.append(True)
                    else:
                        durations.append((observation_end - observation_start) / 86400.0)
                        event_observed.append(False)
            
            history_days = (ts_now - global_first_seen) / 86400.0
                
            life_exp = 0.0
            median_survival = None
            curve = {}
            if history_days >= 30 and durations:
                curve = CommunityModels.calculate_survival_rate(durations, event_observed)
                life_exp = CommunityModels.estimate_life_expectancy(curve)
                median_survival = CommunityModels.estimate_median_survival(curve)
            elif durations:
                curve = {}
                life_exp = None
                median_survival = None
                
            # Převod stavů pro API
            dist_dict = {
                "new": current_distribution[UserState.NEW.value],
                "active": current_distribution[UserState.ACTIVE.value],
                "passive": current_distribution[UserState.PASSIVE.value],
                "inactive": current_distribution[UserState.INACTIVE.value]
            }
            
            future_dist_api = {
                "available": predicted_distribution_available,
                "reason": predicted_distribution_reason,
                "distribution": future_dist
            } if not predicted_distribution_available else future_dist
                
            return {
                "success": True,
                "activity_rate_pct": round(activity_rate * 100, 1) if activity_rate is not None else None,
                "mii": round(mii, 4) if mii is not None else None,
                "mii_window_days": 30,
                "mii_weighted_actions": weighted_mod_actions,
                "mii_interactions": total_interactions_30d,
                "retention_pct": round(p_stay_active * 100, 1) if p_stay_active is not None else None,
                "inactivity_risk_pct": round(p_inactive * 100, 1) if p_inactive is not None else None,
                "activity_survival_expectancy_days": round(life_exp, 1) if life_exp is not None else None,
                "median_activity_survival_days": median_survival,
                "survival_event": "first_inactivity_period",
                "inactivity_threshold_days": ACTIVITY_INACTIVITY_THRESHOLD_DAYS,
                "survival_basis": "observed_activity",
                "new_state_basis": global_new_state_basis,
                "state_distribution": dist_dict,
                "predicted_distribution": future_dist_api,
                "survival_curve": curve
            }
        except Exception as e:
            print(f"Error computing health research data: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    async def get_channel_activity(self, guild_id: int, start_date: str = None, end_date: str = None, platform: str = "all", channel_id: str = None, topic_id: str = None):
        import json
        from collections import defaultdict
        
        r = await self.repo.get_client()
        
        if not start_date or not end_date:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=30)
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
        ts_start = start_dt.timestamp()
        ts_end = end_dt.replace(hour=23, minute=59, second=59).timestamp()
        
        channel_stats = defaultdict(lambda: {"messages": 0, "reactions": 0, "active_users": set(), "platform": "discord"})
        
        # Discord events
        if platform in ["all", "discord"]:
            async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
                if ":discourse" in key:
                    continue
                uid = key.split(":")[-1]
                events = await r.zrangebyscore(key, ts_start, ts_end)
                for e in events:
                    try:
                        data = json.loads(e)
                        c_id = str(data.get("channel_id"))
                        if not c_id or c_id == "None":
                            continue
                        if channel_id and c_id != channel_id:
                            continue
                        channel_stats[c_id]["messages"] += 1
                        channel_stats[c_id]["reactions"] += int(data.get("reaction_count", 0))
                        channel_stats[c_id]["active_users"].add(uid)
                    except:
                        pass
        
        # Discourse events
        if platform in ["all", "discourse"]:
            discourse_key = f"events:msg:{guild_id}:discourse"
            events = await r.zrangebyscore(discourse_key, ts_start, ts_end)
            for e in events:
                try:
                    data = json.loads(e)
                    tpc_id = str(data.get("id"))
                    if not tpc_id or tpc_id == "None":
                        continue
                    if topic_id and tpc_id != topic_id:
                        continue
                    channel_stats[tpc_id]["messages"] += 1
                    channel_stats[tpc_id]["reactions"] += int(data.get("reaction_count", 0))
                    channel_stats[tpc_id]["platform"] = "discourse"
                    
                except:
                    pass
                    
        result = []
        for cid, stats in channel_stats.items():
            result.append({
                "channel_id": cid,
                "platform": stats["platform"],
                "messages": stats["messages"],
                "reactions": stats["reactions"],
                "active_users": len(stats["active_users"])
            })
            
        result.sort(key=lambda x: x["messages"], reverse=True)
        return result

    async def get_community_health_support(self, guild_id: int, days: int = 30):
        import json
        r = await self.repo.get_client()
        
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)
        ts_start = start_dt.timestamp()
        ts_end = end_dt.timestamp()
        
        cfg_str = await r.get(f"config:settings:{guild_id}")
        support_channels = []
        support_mode = "question_only"
        
        if cfg_str:
            try:
                cfg = json.loads(cfg_str)
                support_channels = cfg.get("support_channels", [])
                support_mode = cfg.get("support_detection_mode", "question_only")
            except:
                pass
                
        # If no config, maybe use a default or empty. We need it to be configurable.
        # But if empty, we might return empty dict or zeroes.
        
        requests = {}
        replies = []
        
        async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
            if ":discourse" in key:
                continue
            uid = key.split(":")[-1]
            # Fetch even outside of range for replies? Yes, up to now.
            events = await r.zrangebyscore(key, ts_start, ts_end + (days*86400)) # get future replies too
            
            for e, score in await r.zrangebyscore(key, ts_start, ts_end + (30*86400), withscores=True):
                try:
                    data = json.loads(e)
                    mid = data.get("mid")
                    c_id = str(data.get("channel_id"))
                    is_reply = data.get("reply")
                    reply_to = data.get("reply_to_mid")
                    is_question = data.get("is_question")
                    reactions = int(data.get("reaction_count", 0))
                    
                    if is_reply and reply_to:
                        replies.append({"mid": mid, "reply_to": reply_to, "ts": score, "author": uid})
                    
                    # check if request
                    if ts_start <= score <= ts_end: # request must be in the window
                        if not support_channels:
                            return {"available": False, "reason": "support_channels_not_configured"}
                        if c_id in support_channels:
                            is_relevant = True
                            if support_mode == "question_only" and not is_question:
                                is_relevant = False
                            if is_relevant and not is_reply: # Request shouldn't be a reply itself usually, or can be.
                                requests[mid] = {"ts": score, "author": uid, "first_response_time": None, "reactions": reactions}
                except:
                    pass
        
        # Evaluate replies
        # Sort replies by timestamp
        replies.sort(key=lambda x: x["ts"])
        
        for reply in replies:
            req_id = reply["reply_to"]
            if req_id in requests:
                req = requests[req_id]
                if req["first_response_time"] is None and reply["author"] != req["author"]:
                    req["first_response_time"] = reply["ts"] - req["ts"]
                    
        total_requests = len(requests)
        answered = 0
        response_times = []
        total_reactions = 0
        
        for mid, req in requests.items():
            total_reactions += req["reactions"]
            if req["first_response_time"] is not None:
                answered += 1
                response_times.append(req["first_response_time"])
                
        open_reqs = total_requests - answered
        answered_ratio = answered / total_requests if total_requests > 0 else 0
        
        import statistics
        median_response = statistics.median(response_times) if response_times else None
        avg_response = statistics.mean(response_times) if response_times else None
        
        return {
            "requests": total_requests,
            "answered": answered,
            "open": open_reqs,
            "answered_ratio": round(answered_ratio, 2),
            "median_first_response_time": median_response,
            "average_first_response_time": avg_response,
            "requests_with_reaction": sum(1 for r in requests.values() if r["reactions"] > 0),
            "average_reactions": round(total_reactions / total_requests, 2) if total_requests > 0 else 0,
            "support_channels_configured": len(support_channels) > 0,
            "support_mode": support_mode
        }

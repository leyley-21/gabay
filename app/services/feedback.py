"""Feedback storage and deterministic summary calculation."""
FEEDBACK_TYPES = {'helpful', 'not_relevant', 'clicked_onet_profile', 'engaged_reading_30s', 'quick_retake_mismatch'}

def rebuild_summary(db):
    # Rebuild in the caller's transaction, so deleted/replaced votes cannot leave stale scores.
    db.execute('DELETE FROM job_feedback_summary')
    db.execute("""INSERT INTO job_feedback_summary
        (onet_code, riasec_cluster, user_goal, total_interactions, net_score_boost)
        SELECT onet_code, COALESCE(riasec_cluster, ''), COALESCE(user_goal, ''), COUNT(*),
            ROUND(SUM(CASE feedback_type WHEN 'helpful' THEN 1.0
            WHEN 'clicked_onet_profile' THEN 0.5 WHEN 'engaged_reading_30s' THEN 0.2
            WHEN 'not_relevant' THEN -1.0 ELSE 0.0 END), 2)
        FROM raw_feedback_logs WHERE onet_code NOT IN ('APP_RETAKE', 'UNKNOWN_CODE')
        GROUP BY onet_code, COALESCE(riasec_cluster, ''), COALESCE(user_goal, '')""")
    return db.execute('SELECT COUNT(*) FROM job_feedback_summary').fetchone()[0]

def record_feedback(db, data):
    opposite = {'helpful': 'not_relevant', 'not_relevant': 'helpful'}.get(data['feedback_type'])
    with db:
        db.execute('BEGIN IMMEDIATE')
        # Capture old groups before changing a vote's profile or polarity.
        affected = {tuple(row) for row in db.execute(
            "SELECT onet_code,COALESCE(riasec_cluster,''),COALESCE(user_goal,'') FROM raw_feedback_logs "
            'WHERE session_id=? AND onet_code=? AND feedback_type IN (?,?)',
            (data['session_id'],data['onet_code'],data['feedback_type'],opposite or data['feedback_type']))}
        affected.add((data['onet_code'],data.get('riasec_cluster',''),data.get('goal','')))
        if opposite:
            db.execute('DELETE FROM raw_feedback_logs WHERE session_id=? AND onet_code=? AND feedback_type=?',
                (data['session_id'], data['onet_code'], opposite))
        db.execute("""INSERT INTO raw_feedback_logs
            (session_id, onet_code, user_goal, education_level, riasec_cluster, feedback_type)
            VALUES (?,?,?,?,?,?) ON CONFLICT(session_id, onet_code, feedback_type) DO UPDATE SET
            timestamp=CURRENT_TIMESTAMP, user_goal=excluded.user_goal,
            education_level=excluded.education_level, riasec_cluster=excluded.riasec_cluster""",
            (data['session_id'], data['onet_code'], data.get('goal',''), data.get('education',''),
             data.get('riasec_cluster',''), data['feedback_type']))
        for code, cluster, goal in affected:
            db.execute('DELETE FROM job_feedback_summary WHERE onet_code=? AND riasec_cluster=? AND user_goal=?',
                       (code,cluster,goal))
            if code in ('APP_RETAKE','UNKNOWN_CODE'):
                continue
            db.execute("""INSERT INTO job_feedback_summary
                (onet_code,riasec_cluster,user_goal,total_interactions,net_score_boost)
                SELECT onet_code,COALESCE(riasec_cluster,''),COALESCE(user_goal,''),COUNT(*),
                    ROUND(SUM(CASE feedback_type WHEN 'helpful' THEN 1.0
                    WHEN 'clicked_onet_profile' THEN 0.5 WHEN 'engaged_reading_30s' THEN 0.2
                    WHEN 'not_relevant' THEN -1.0 ELSE 0.0 END),2)
                FROM raw_feedback_logs
                WHERE onet_code=? AND COALESCE(riasec_cluster,'')=? AND COALESCE(user_goal,'')=?
                GROUP BY onet_code,COALESCE(riasec_cluster,''),COALESCE(user_goal,'')""", (code,cluster,goal))

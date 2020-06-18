
LOAD_RECIPIENTS_SQL = """SELECT id
FROM handle AS H
    INNER JOIN chat_handle_join AS CHJ
        ON H.ROWID = CHJ.handle_id
        AND CHJ.chat_id = ?"""

LOAD_MESSAGES_SQL = """SELECT {}
FROM message
    INNER JOIN chat_message_join
        ON message.ROWID = chat_message_join.message_id
        AND chat_message_join.chat_id = ?
    INNER JOIN message_update_date_join
        ON message.ROWID = message_update_date_join.message_id
        AND message_update_date_join.message_update_date > ?
    LEFT JOIN message_attachment_join
        ON message.ROWID = message_attachment_join.message_id"""

HANDLE_SQL = """SELECT id
FROM handle
    WHERE ROWID = ?"""

ATTACHMENT_SQL = """SELECT filename, uti
FROM attachment
    WHERE ROWID = ?"""

ASSOC_MESSAGE_SQL = """SELECT ROWID
FROM message
    WHERE guid = ?"""

RECENT_MESSAGE_SQL = """SELECT ROWID, handle_id, text, date, is_from_me,
                        associated_message_guid, associated_message_type,
                        is_delivered, is_from_me
FROM message
    INNER JOIN chat_message_join AS CMJ
        ON message.ROWID = CMJ.message_id
        AND CMJ.chat_id = ?
    ORDER BY date DESC, ROWID DESC"""

LOAD_CHAT_SQL = """SELECT ROWID, chat_identifier, display_name, style,
                   service_name
FROM chat
    WHERE ROWID = ?"""

LOAD_CHATS_SQL = """SELECT ROWID, chat_identifier, display_name, style
FROM chat"""

CHATS_TO_UPDATE_SQL = """SELECT chat_id, max(message_update_date), text
FROM message
    INNER JOIN chat_message_join as CMJ
        ON message.ROWID = CMJ.message_id
    INNER JOIN message_update_date_join as MUDJ
        ON message.ROWID = MUDJ.message_id
        AND MUDJ.message_update_date > ?
    GROUP BY chat_id"""

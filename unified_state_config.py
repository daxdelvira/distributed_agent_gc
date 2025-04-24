ONE_VAR_STATE = {
    "writer_topic_1": "None",
}

FIVE_VAR_STATE = {
    "writer_topic_1": "None",
    "writer_total_lines_written_1": 0,
    "editor_feedback_addressed_1": True,
    "editor_num_lines_edited_1": 0,
    "editor_feedback_positive_1": True,
}

TEN_VAR_STATE = {
    "writer_topic_1": "None",
    "writer_total_lines_written_1": 0,
    "editor_feedback_addressed_1": True,
    "editor_num_lines_edited_1": 0,
    "editor_feedback_positive_1": True,
    "writer_topic_2": "None",
    "writer_total_lines_written_2": 0,
    "editor_feedback_addressed_2": True,
    "editor_num_lines_edited_2": 0,
    "editor_feedback_positive_2": True,
}

FIFTY_VAR_STATE = {
    f"writer_topic_{i}": "None" for i in range(1, 11)
} | {
    f"writer_total_lines_written_{i}": 0 for i in range(1, 11)
} | {
    f"editor_feedback_addressed_{i}": True for i in range(1, 11)
} | {
    f"editor_num_lines_edited_{i}": 0 for i in range(1, 11)
} | {
    f"editor_feedback_positive_{i}": True for i in range(1, 11)
}

HUNDRED_VAR_STATE = {
    f"writer_topic_{i}": "None" for i in range(1, 21)
} | {
    f"writer_total_lines_written_{i}": 0 for i in range(1, 21)
} | {
    f"editor_feedback_addressed_{i}": True for i in range(1, 20 + 1)
} | {
    f"editor_num_lines_edited_{i}": 0 for i in range(1, 20 + 1)
} | {
    f"editor_feedback_positive_{i}": True for i in range(1, 20 + 1)
}

#!/usr/bin/env python3

import sys
import os
import re
import csv
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Parse moodle format into html format.')
    parser.add_argument('--disable_q_num', action='store_true', default=False,
                        help='Disable question numbering.')
    parser.add_argument('--meta_csv_path', required=True,
                        help='Output path for the meta data csv file.')
    parser.add_argument('--html_path', required=True,
                        help='Output path for the generated html file.')
    parser.add_argument('moodle_question_dir', 
                        help='Question directory to moodle export data.')
    args = parser.parse_args()
    return args

def parse_choices(raw_choices):
    lines = raw_choices.strip().split('\n')

    if lines[0] != '{' or lines[-1] != '}':
        raise Exception('Choices section is not formatted as expected.')

    choices = lines[1:-1]
    return choices

def clear_image_prefix(output_content):
    clean_output_content = output_content.replace('src\="@@PLUGINFILE@@/', 'src="')
    return clean_output_content 

def parse_questions(output_content):
    pattern = r'^(.*)((?:.+\n)+)'
    prog = re.compile(pattern, re.MULTILINE)
    questions = []
    prev_end = -1
    while (match := prog.match(output_content, prev_end + 1)) != None:
        question = {
            'raw': match.group(0),
            'question': match.group(1),
            'choices': parse_choices(match.group(2)),
        }
        questions.append(question)
        prev_end = match.end()
    return questions

def generate_question_section(context, question):
    if 'question_number' not in context:
        context['question_number'] = 1
    if not context['args'].disable_q_num:
        question_number = context['question_number']
        context['question_number'] += 1
        return '{}. {}'.format(question_number, question)
    return question

def generate_choices_section(choices):
    section = ''
    for choice in choices:
        section += '<li>{}</li>\n'.format(choice.strip().lstrip('~='))
    return section

def generate_html(context, questions):
    html = ''

    html += '<html>'
    html += '''
            <head>
                <style type="text/css">
                img {
                  height: auto;
                  width: auto;
                  max-width: 500px;
                  max-height: 500px;
                }
                </style>
            </head>
            '''
    for question in questions:
        html += '<div class="question">{}<ol type="A">{}</ol></div>'.format(
                generate_question_section(context, question['question']),
                generate_choices_section(question['choices']))
        html += '<br/>'
    html += '</html>'
    return html

def get_answer_choice_ids(choices):
    answers = []
    choice_id = 0
    for choice in choices:
        if choice.strip().startswith('='):
            answers.append(str(choice_id + 1))
        choice_id += 1
    return answers

def generate_meta_data(context, questions):
    with open(context['args'].meta_csv_path, 'w', newline='') as csvfile:
        fieldnames = ['q_num', 'choices_num', 'answer', 'score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        q_num = 1
        for question in questions:
            answer_choice_ids = get_answer_choice_ids(question['choices'])
            writer.writerow({'q_num': str(q_num),
                             'choices_num': len(question['choices']),
                             'answer': '_'.join(answer_choice_ids),
                             'score': str(10)})
            q_num += 1
    return

def main():
    args = parse_args()
    context = {
        'args': args,
    }

    moodle_output_txt = os.path.join(args.moodle_question_dir, 'output.txt')
    with open(moodle_output_txt, 'r') as f:
        raw_data = f.read()
        raw_data = clear_image_prefix(raw_data)
        questions = parse_questions(raw_data)
        html = generate_html(context, questions)

        with open(args.html_path, 'w') as html_file:
            html_file.write(html)

        generate_meta_data(context, questions)

if __name__ == '__main__':
    main()

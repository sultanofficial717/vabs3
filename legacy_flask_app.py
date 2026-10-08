# -*- coding: utf-8 -*-
"""
app.py
======
Flask web server for the Vineland-3 (VABS-3) Assessment System demo.

Routes:
  GET  /           -> render the single-page UI (with item metadata)
  POST /calculate  -> score raw or item-level responses; return scores + ASD patterns
  POST /patterns   -> run the ASD pattern engine on scores + item responses
  POST /interpret  -> call the Groq API; return the 8-section narrative + patterns
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template, request, jsonify
import meta
import scoring
import items as item_defs
import pattern_engine
import age_markers
from interpreter import generate_interpretation, InterpreterError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
)


def check_groq_key():
    """Return True only when a real Groq API key is configured."""
    key = os.environ.get('GROQ_API_KEY', '')
    if not key or key == 'your_actual_key_here':
        print('[WARNING] GROQ_API_KEY not set. AI interpretation disabled.')
        return False
    return True


GROQ_AVAILABLE = check_groq_key()


def _item_data():
    subs = {}
    for code in meta.SUBDOMAINS:
        subs[code] = item_defs.item_meta(code)

    maladaptive = {
        'int': [{'num': i + 1, 'desc': d} for i, d in enumerate(item_defs.INTERNALIZING)],
        'ext': [{'num': i + 1, 'desc': d} for i, d in enumerate(item_defs.EXTERNALIZING)],
        'critical': [{'num': i + 1, 'desc': d, 'urgent': (i + 1) in item_defs.URGENT_CRITICAL} for i, d in enumerate(item_defs.CRITICAL)],
    }
    return {
        'subdomains': subs,
        'maladaptive': maladaptive,
    }


@app.route('/')
def index():
    return render_template(
        'index.html',
        domains=meta.DOMAINS,
        subdomains=meta.SUBDOMAINS,
        maladaptive=meta.MALADAPTIVE,
        max_raw=meta.max_raw,
        item_data=_item_data(),
    )


def _patterns_for(result):
    flat = result.get('flat', {})
    scores = {
        'com_ss': flat.get('com_ss', 100),
        'dls_ss': flat.get('dls_ss', 100),
        'soc_ss': flat.get('soc_ss', 100),
        'mot_ss': flat.get('mot_ss', 100),
        'abc': flat.get('abc', 100),
    }
    item_responses = dict(result.get('resolved_items', {}))
    mal = result.get('maladaptive', {})
    if mal.get('provided') and mal.get('critical_scores'):
        item_responses['critical'] = mal['critical_scores']
    return pattern_engine.analyze_asd_patterns(scores, item_responses or None)


@app.route('/age_markers', methods=['GET'])
def age_markers_route():
    return jsonify(age_markers.AGE_MARKERS)


@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json(silent=True) or {}
    patient_info = data.get('patient_info', {})
    raw_scores = data.get('raw_scores', {})
    item_responses = data.get('item_responses', {})
    maladaptive = data.get('maladaptive', {})

    try:
        result = scoring.calculate_scores(raw_scores, patient_info, item_responses, maladaptive)
        patterns = _patterns_for(result)
        return jsonify({
            'ok': True,
            'success': True,
            'scores': result,
            'patterns': patterns,
            'scoring_source': scoring.SCORING_SOURCE,
        })
    except Exception as exc:
        return jsonify({
            'ok': False,
            'success': False,
            'error': 'Scoring failed: {}'.format(exc),
        }), 400


@app.route('/patterns', methods=['POST'])
def patterns():
    data = request.get_json(silent=True) or {}
    scores_in = data.get('scores', {})
    item_responses = data.get('item_responses', None)

    if isinstance(scores_in, dict) and 'flat' in scores_in:
        flat = scores_in['flat']
        if item_responses is None:
            item_responses = scores_in.get('resolved_items', None)
    else:
        flat = scores_in or {}

    scores = {
        'com_ss': flat.get('com_ss', 100),
        'dls_ss': flat.get('dls_ss', 100),
        'soc_ss': flat.get('soc_ss', 100),
        'mot_ss': flat.get('mot_ss', 100),
        'abc': flat.get('abc', 100),
    }

    try:
        analysis = pattern_engine.analyze_asd_patterns(scores, item_responses or None)
        return jsonify({
            'ok': True,
            'patterns': analysis,
        })
    except Exception as exc:
        return jsonify({
            'ok': False,
            'error': 'Pattern analysis failed: {}'.format(exc),
        }), 400


@app.route('/interpret', methods=['POST'])
def interpret():
    data = request.get_json(silent=True) or {}
    patient_info = data.get('patient_info', {})
    result = data.get('scores', {})

    if not check_groq_key():
        return jsonify({
            'ok': False,
            'error': 'AI interpretation is unavailable. The GROQ_API_KEY is missing from the .env file. Please contact the system administrator.',
            'narrative': 'AI interpretation is unavailable. The GROQ_API_KEY is missing from the .env file. Please contact the system administrator.',
            'disclaimer': 'This system requires a valid API key for AI features.',
        }), 200

    try:
        analysis = _patterns_for(result) if result.get('flat') else None
        narrative = generate_interpretation(result, patient_info, analysis)
        return jsonify({
            'ok': True,
            'narrative': narrative,
            'patterns': analysis,
        })
    except InterpreterError as exc:
        return jsonify({
            'ok': False,
            'error': str(exc),
        }), 502
    except Exception as exc:
        return jsonify({
            'ok': False,
            'error': 'Unexpected error: {}'.format(exc),
        }), 500


if __name__ == '__main__':
    key = os.environ.get('GROQ_API_KEY', '')
    if key:
        print("[startup] GROQ_API_KEY detected (starts with '{}...', length {}).".format(key[:4], len(key)))
    else:
        print('[startup] WARNING: GROQ_API_KEY is NOT set in this process. AI interpretation will fail until it is set in .env.')
    app.run(host='0.0.0.0', port=5050, debug=True, use_reloader=False)

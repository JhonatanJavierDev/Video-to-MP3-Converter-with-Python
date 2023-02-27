from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import os
import ffmpeg

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024 # límite de tamaño de archivo en 30 MB esto lo puedes cambiar

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(filename)
            output_file = os.path.splitext(filename)[0] + '.mp3'
            try:
                stream = ffmpeg.input(filename)
                stream = ffmpeg.output(stream, output_file)
                process = ffmpeg.run_async(stream, pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
                # barra de progreso
                while True:
                    output = process.stderr.readline()
                    if not output:
                        break
                    progress = output.decode('utf-8').strip()
                    if progress.startswith('frame='):
                        progress = progress.split()[0].split('=')[1]
                        progress = int(progress)
                        total_frames = int(process.duration * process.fps)
                        percentage = int(progress / total_frames * 100)
                        progress_message = 'Progreso: {}%'.format(percentage)
                        print(progress_message)
                        # Mostramos el proceso al cliente
                        socketio.emit('progress', {'data': progress_message}, namespace='/test')
                print('Archivo convertido con éxito.')
            except ffmpeg.Error as e:
                print('Error al convertir el archivo:', e.stderr.decode('utf8'))
            os.remove(filename)
            return jsonify({'status': 'success'})
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

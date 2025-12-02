document.addEventListener('DOMContentLoaded', () => {
    const inputText = document.getElementById('inputText');
    const personaBtns = document.querySelectorAll('.persona-btn');
    const convertBtn = document.getElementById('convertBtn');
    const resultText = document.getElementById('resultText');
    const copyBtn = document.getElementById('copyBtn');

    let selectedPersona = 'boss'; // Default persona

    // Persona selection logic
    personaBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            personaBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedPersona = btn.dataset.persona;
        });
    });

    // Convert button logic
    convertBtn.addEventListener('click', async () => {
        const text = inputText.value;
        if (!text.trim()) {
            alert('변환할 내용을 입력하세요.');
            return;
        }

        resultText.innerText = '변환 중...';

        try {
            const response = await fetch('https://business-tone-converter-nocq3sdxqq-du.a.run.app/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    persona: selectedPersona,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if(data.error) {
                resultText.innerText = `오류가 발생했습니다: ${data.error}`;
            } else {
                resultText.innerText = data.transformed_text;
            }

        } catch (error) {
            console.error('Error:', error);
            resultText.innerText = '변환 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';
        }
    });

    // Copy button logic
    copyBtn.addEventListener('click', () => {
        if (resultText.innerText && resultText.innerText !== '변환 중...') {
            navigator.clipboard.writeText(resultText.innerText)
                .then(() => alert('클립보드에 복사되었습니다.'))
                .catch(err => console.error('Copy failed', err));
        }
    });
});

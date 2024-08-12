llama-server \
-m /home/student/anurag/.models/gemma-2-9b-it-Q4_K_M.gguf \
-cb \
-t 12 \
-c 2000 \
-n 1800 \
--port 8080 \
--host :: \
--threads-http 12 \
--grammar-file /home/student/anurag/dss-solar-selc/categorize/theme/grammar/theme_grammar.gbnf

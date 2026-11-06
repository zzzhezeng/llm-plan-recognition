# LLMs as recognizers on the CLARA grid benchmarks

Data: HenryKautz/CLARA at the commit in `data/clara/SOURCE_COMMIT.txt`. **Accuracy** scores a run 1/k when the true goal is among k goals tied for the highest probability, else 0. **P(true)** is the probability given to the true goal. Both are means over answered files, averaging a file's valid samples, and methods answered different files, so compare them in the same-file table. **Chance** is 1 / number of goals. Recognizer rows come from CLARA's own run records. **stop-rule** is a baseline that needs no model: it spreads the probability over the goals already true when the observations stop. Every plan ends as soon as its goal holds, so it scores 1.0 with the whole plan; at 25% no goal is true yet, so it scores chance.

## Models

| model | calls | returned | errors | timeouts | valid | valid rate | cut off | in tok | out tok | reason tok | latency s | cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-5.4-mini | 3744 | 3744 | 0 | 0 | 3744 | 1.00 | 0 | 3075 | 245 | 0 | 1.8 | $12.77 |
| gpt-6-luna | 3744 | 3744 | 0 | 0 | 3744 | 1.00 | 0 | 3075 | 1721 | 1529 | 18.2 | $4.37 |
| hf:Qwen/Qwen2.5-7B-Instruct | 3744 | 3744 | 0 | 0 | 3702 | 0.99 | 0 | 3088 | 201 | – | 3.1 | $0.00 |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | 3744 | 3744 | 0 | 0 | 3590 | 0.96 | 0 | 3080 | 132 | – | 2.2 | $0.00 |
| jev-latest | 3744 | 3744 | 0 | 0 | 3744 | 1.00 | 0 | 3367 | 76 | – | 0.1 | $0.00 |

## By family and evidence

| family | evidence | method | files | accuracy | P(true) | chance |
|---|---|---|---|---|---|---|
| SimpleGrid | 25% | gpt-5.4-mini | 176/176 | 0.184 | 0.182 | 0.182 |
| SimpleGrid | 25% | gpt-6-luna | 176/176 | 0.203 | 0.198 | 0.182 |
| SimpleGrid | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 176/176 | 0.207 | 0.188 | 0.182 |
| SimpleGrid | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 176/176 | 0.161 | 0.177 | 0.182 |
| SimpleGrid | 25% | jev-latest | 176/176 | 0.214 | 0.187 | 0.182 |
| SimpleGrid | 25% | max-term | 176/176 | 0.187 | 0.186 | 0.182 |
| SimpleGrid | 25% | sharpsat-td | 79/176 | 0.304 | 0.278 | 0.251 |
| SimpleGrid | 25% | mc-sat | 41/176 | 0.366 | 0.343 | 0.311 |
| SimpleGrid | 25% | stop-rule | 176/176 | 0.182 | 0.182 | 0.182 |
| SimpleGrid | 100% | gpt-5.4-mini | 176/176 | 0.924 | 0.800 | 0.182 |
| SimpleGrid | 100% | gpt-6-luna | 176/176 | 0.884 | 0.655 | 0.182 |
| SimpleGrid | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 176/176 | 0.596 | 0.474 | 0.182 |
| SimpleGrid | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 176/176 | 0.243 | 0.208 | 0.182 |
| SimpleGrid | 100% | jev-latest | 176/176 | 0.860 | 0.557 | 0.182 |
| SimpleGrid | 100% | max-term | 176/176 | 0.545 | 0.510 | 0.182 |
| SimpleGrid | 100% | sharpsat-td | 63/176 | 0.317 | 0.422 | 0.272 |
| SimpleGrid | 100% | mc-sat | 39/176 | 0.564 | 0.621 | 0.318 |
| SimpleGrid | 100% | stop-rule | 176/176 | 1.000 | 1.000 | 0.182 |
| TwoPackage | 25% | gpt-5.4-mini | 80/80 | 0.354 | 0.315 | 0.250 |
| TwoPackage | 25% | gpt-6-luna | 80/80 | 0.438 | 0.435 | 0.250 |
| TwoPackage | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 80/80 | 0.275 | 0.259 | 0.250 |
| TwoPackage | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 80/80 | 0.253 | 0.260 | 0.250 |
| TwoPackage | 25% | jev-latest | 80/80 | 0.377 | 0.310 | 0.250 |
| TwoPackage | 25% | max-term | 80/80 | 0.444 | 0.417 | 0.250 |
| TwoPackage | 25% | sharpsat-td | 16/80 | 0.375 | 0.484 | 0.250 |
| TwoPackage | 25% | mc-sat | 7/80 | 0.429 | 0.446 | 0.250 |
| TwoPackage | 25% | stop-rule | 80/80 | 0.250 | 0.250 | 0.250 |
| TwoPackage | 100% | gpt-5.4-mini | 80/80 | 1.000 | 0.927 | 0.250 |
| TwoPackage | 100% | gpt-6-luna | 80/80 | 1.000 | 0.997 | 0.250 |
| TwoPackage | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 80/80 | 0.772 | 0.651 | 0.250 |
| TwoPackage | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 80/80 | 0.328 | 0.281 | 0.250 |
| TwoPackage | 100% | jev-latest | 80/80 | 1.000 | 0.914 | 0.250 |
| TwoPackage | 100% | max-term | 80/80 | 1.000 | 0.982 | 0.250 |
| TwoPackage | 100% | sharpsat-td | 16/80 | 1.000 | 0.998 | 0.250 |
| TwoPackage | 100% | mc-sat | 10/80 | 1.000 | 0.992 | 0.250 |
| TwoPackage | 100% | stop-rule | 80/80 | 1.000 | 1.000 | 0.250 |
| TwoPackageOneway | 25% | gpt-5.4-mini | 80/80 | 0.340 | 0.312 | 0.250 |
| TwoPackageOneway | 25% | gpt-6-luna | 80/80 | 0.415 | 0.418 | 0.250 |
| TwoPackageOneway | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 80/80 | 0.313 | 0.297 | 0.250 |
| TwoPackageOneway | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 80/80 | 0.312 | 0.271 | 0.250 |
| TwoPackageOneway | 25% | jev-latest | 80/80 | 0.398 | 0.310 | 0.250 |
| TwoPackageOneway | 25% | max-term | 80/80 | 0.447 | 0.425 | 0.250 |
| TwoPackageOneway | 25% | sharpsat-td | 20/80 | 0.400 | 0.487 | 0.250 |
| TwoPackageOneway | 25% | mc-sat | 17/80 | 0.235 | 0.296 | 0.250 |
| TwoPackageOneway | 25% | stop-rule | 80/80 | 0.250 | 0.250 | 0.250 |
| TwoPackageOneway | 100% | gpt-5.4-mini | 80/80 | 1.000 | 0.928 | 0.250 |
| TwoPackageOneway | 100% | gpt-6-luna | 80/80 | 1.000 | 0.997 | 0.250 |
| TwoPackageOneway | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 80/80 | 0.740 | 0.636 | 0.250 |
| TwoPackageOneway | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 80/80 | 0.343 | 0.302 | 0.250 |
| TwoPackageOneway | 100% | jev-latest | 80/80 | 1.000 | 0.920 | 0.250 |
| TwoPackageOneway | 100% | max-term | 80/80 | 1.000 | 0.984 | 0.250 |
| TwoPackageOneway | 100% | sharpsat-td | 16/80 | 1.000 | 0.998 | 0.250 |
| TwoPackageOneway | 100% | mc-sat | 16/80 | 1.000 | 0.996 | 0.250 |
| TwoPackageOneway | 100% | stop-rule | 80/80 | 1.000 | 1.000 | 0.250 |
| ThreePackage | 25% | gpt-5.4-mini | 40/40 | 0.151 | 0.144 | 0.125 |
| ThreePackage | 25% | gpt-6-luna | 40/40 | 0.148 | 0.145 | 0.125 |
| ThreePackage | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 40/40 | 0.126 | 0.135 | 0.125 |
| ThreePackage | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 40/40 | 0.143 | 0.133 | 0.125 |
| ThreePackage | 25% | jev-latest | 40/40 | 0.179 | 0.143 | 0.125 |
| ThreePackage | 25% | stop-rule | 40/40 | 0.125 | 0.125 | 0.125 |
| ThreePackage | 100% | gpt-5.4-mini | 40/40 | 0.856 | 0.821 | 0.125 |
| ThreePackage | 100% | gpt-6-luna | 40/40 | 1.000 | 0.998 | 0.125 |
| ThreePackage | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 40/40 | 0.282 | 0.240 | 0.125 |
| ThreePackage | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 40/40 | 0.130 | 0.118 | 0.125 |
| ThreePackage | 100% | jev-latest | 40/40 | 1.000 | 0.921 | 0.125 |
| ThreePackage | 100% | stop-rule | 40/40 | 1.000 | 1.000 | 0.125 |
| FourPackage | 25% | gpt-5.4-mini | 168/168 | 0.172 | 0.131 | 0.083 |
| FourPackage | 25% | gpt-6-luna | 168/168 | 0.301 | 0.274 | 0.083 |
| FourPackage | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 168/168 | 0.112 | 0.098 | 0.083 |
| FourPackage | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 168/168 | 0.095 | 0.085 | 0.083 |
| FourPackage | 25% | jev-latest | 168/168 | 0.240 | 0.162 | 0.083 |
| FourPackage | 25% | max-term | 0/168 | – | – | – |
| FourPackage | 25% | stop-rule | 168/168 | 0.083 | 0.083 | 0.083 |
| FourPackage | 100% | gpt-5.4-mini | 168/168 | 0.988 | 0.905 | 0.083 |
| FourPackage | 100% | gpt-6-luna | 168/168 | 1.000 | 0.996 | 0.083 |
| FourPackage | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 168/168 | 0.500 | 0.397 | 0.083 |
| FourPackage | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 168/168 | 0.110 | 0.093 | 0.083 |
| FourPackage | 100% | jev-latest | 168/168 | 1.000 | 0.938 | 0.083 |
| FourPackage | 100% | stop-rule | 168/168 | 1.000 | 1.000 | 0.083 |

## By size

| family | size | evidence | method | files | accuracy | P(true) | chance |
|---|---|---|---|---|---|---|---|
| SimpleGrid | 3x3 | 25% | gpt-5.4-mini | 8/8 | 0.479 | 0.502 | 0.500 |
| SimpleGrid | 3x3 | 25% | gpt-6-luna | 8/8 | 0.625 | 0.521 | 0.500 |
| SimpleGrid | 3x3 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 8/8 | 0.521 | 0.508 | 0.500 |
| SimpleGrid | 3x3 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 8/8 | 0.510 | 0.500 | 0.500 |
| SimpleGrid | 3x3 | 25% | jev-latest | 8/8 | 0.646 | 0.530 | 0.500 |
| SimpleGrid | 3x3 | 25% | max-term | 8/8 | 0.500 | 0.500 | 0.500 |
| SimpleGrid | 3x3 | 25% | sharpsat-td | 8/8 | 0.688 | 0.563 | 0.500 |
| SimpleGrid | 3x3 | 25% | mc-sat | 8/8 | 0.750 | 0.570 | 0.500 |
| SimpleGrid | 3x3 | 25% | stop-rule | 8/8 | 0.500 | 0.500 | 0.500 |
| SimpleGrid | 3x3 | 100% | gpt-5.4-mini | 8/8 | 1.000 | 0.944 | 0.500 |
| SimpleGrid | 3x3 | 100% | gpt-6-luna | 8/8 | 0.896 | 0.812 | 0.500 |
| SimpleGrid | 3x3 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 8/8 | 0.938 | 0.802 | 0.500 |
| SimpleGrid | 3x3 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 8/8 | 0.688 | 0.586 | 0.500 |
| SimpleGrid | 3x3 | 100% | jev-latest | 8/8 | 0.979 | 0.802 | 0.500 |
| SimpleGrid | 3x3 | 100% | max-term | 8/8 | 0.750 | 0.750 | 0.500 |
| SimpleGrid | 3x3 | 100% | sharpsat-td | 8/8 | 0.500 | 0.667 | 0.500 |
| SimpleGrid | 3x3 | 100% | mc-sat | 8/8 | 0.625 | 0.704 | 0.500 |
| SimpleGrid | 3x3 | 100% | stop-rule | 8/8 | 1.000 | 1.000 | 0.500 |
| SimpleGrid | 4x4 | 25% | gpt-5.4-mini | 12/12 | 0.292 | 0.331 | 0.333 |
| SimpleGrid | 4x4 | 25% | gpt-6-luna | 12/12 | 0.356 | 0.322 | 0.333 |
| SimpleGrid | 4x4 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 12/12 | 0.282 | 0.312 | 0.333 |
| SimpleGrid | 4x4 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 12/12 | 0.282 | 0.323 | 0.333 |
| SimpleGrid | 4x4 | 25% | jev-latest | 12/12 | 0.361 | 0.336 | 0.333 |
| SimpleGrid | 4x4 | 25% | max-term | 12/12 | 0.333 | 0.333 | 0.333 |
| SimpleGrid | 4x4 | 25% | sharpsat-td | 12/12 | 0.333 | 0.333 | 0.333 |
| SimpleGrid | 4x4 | 25% | mc-sat | 12/12 | 0.250 | 0.330 | 0.333 |
| SimpleGrid | 4x4 | 25% | stop-rule | 12/12 | 0.333 | 0.333 | 0.333 |
| SimpleGrid | 4x4 | 100% | gpt-5.4-mini | 12/12 | 1.000 | 0.888 | 0.333 |
| SimpleGrid | 4x4 | 100% | gpt-6-luna | 12/12 | 0.944 | 0.776 | 0.333 |
| SimpleGrid | 4x4 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 12/12 | 0.708 | 0.605 | 0.333 |
| SimpleGrid | 4x4 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 12/12 | 0.347 | 0.330 | 0.333 |
| SimpleGrid | 4x4 | 100% | jev-latest | 12/12 | 1.000 | 0.752 | 0.333 |
| SimpleGrid | 4x4 | 100% | max-term | 12/12 | 0.667 | 0.667 | 0.333 |
| SimpleGrid | 4x4 | 100% | sharpsat-td | 12/12 | 0.333 | 0.500 | 0.333 |
| SimpleGrid | 4x4 | 100% | mc-sat | 12/12 | 0.417 | 0.560 | 0.333 |
| SimpleGrid | 4x4 | 100% | stop-rule | 12/12 | 1.000 | 1.000 | 0.333 |
| SimpleGrid | 5x5 | 25% | gpt-5.4-mini | 16/16 | 0.271 | 0.257 | 0.250 |
| SimpleGrid | 5x5 | 25% | gpt-6-luna | 16/16 | 0.302 | 0.293 | 0.250 |
| SimpleGrid | 5x5 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.323 | 0.276 | 0.250 |
| SimpleGrid | 5x5 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.171 | 0.232 | 0.250 |
| SimpleGrid | 5x5 | 25% | jev-latest | 16/16 | 0.250 | 0.257 | 0.250 |
| SimpleGrid | 5x5 | 25% | max-term | 16/16 | 0.250 | 0.250 | 0.250 |
| SimpleGrid | 5x5 | 25% | sharpsat-td | 16/16 | 0.312 | 0.297 | 0.250 |
| SimpleGrid | 5x5 | 25% | mc-sat | 11/16 | 0.364 | 0.350 | 0.250 |
| SimpleGrid | 5x5 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| SimpleGrid | 5x5 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.859 | 0.250 |
| SimpleGrid | 5x5 | 100% | gpt-6-luna | 16/16 | 0.944 | 0.741 | 0.250 |
| SimpleGrid | 5x5 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.812 | 0.683 | 0.250 |
| SimpleGrid | 5x5 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.273 | 0.263 | 0.250 |
| SimpleGrid | 5x5 | 100% | jev-latest | 16/16 | 0.979 | 0.706 | 0.250 |
| SimpleGrid | 5x5 | 100% | max-term | 16/16 | 0.646 | 0.633 | 0.250 |
| SimpleGrid | 5x5 | 100% | sharpsat-td | 16/16 | 0.375 | 0.485 | 0.250 |
| SimpleGrid | 5x5 | 100% | mc-sat | 12/16 | 0.750 | 0.756 | 0.250 |
| SimpleGrid | 5x5 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| SimpleGrid | 6x6 | 25% | gpt-5.4-mini | 20/20 | 0.196 | 0.193 | 0.200 |
| SimpleGrid | 6x6 | 25% | gpt-6-luna | 20/20 | 0.280 | 0.227 | 0.200 |
| SimpleGrid | 6x6 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 20/20 | 0.204 | 0.199 | 0.200 |
| SimpleGrid | 6x6 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20/20 | 0.206 | 0.215 | 0.200 |
| SimpleGrid | 6x6 | 25% | jev-latest | 20/20 | 0.217 | 0.204 | 0.200 |
| SimpleGrid | 6x6 | 25% | max-term | 20/20 | 0.202 | 0.202 | 0.200 |
| SimpleGrid | 6x6 | 25% | sharpsat-td | 20/20 | 0.350 | 0.239 | 0.200 |
| SimpleGrid | 6x6 | 25% | mc-sat | 10/20 | 0.200 | 0.170 | 0.200 |
| SimpleGrid | 6x6 | 25% | stop-rule | 20/20 | 0.200 | 0.200 | 0.200 |
| SimpleGrid | 6x6 | 100% | gpt-5.4-mini | 20/20 | 0.967 | 0.803 | 0.200 |
| SimpleGrid | 6x6 | 100% | gpt-6-luna | 20/20 | 0.898 | 0.642 | 0.200 |
| SimpleGrid | 6x6 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 20/20 | 0.700 | 0.557 | 0.200 |
| SimpleGrid | 6x6 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 20/20 | 0.217 | 0.208 | 0.200 |
| SimpleGrid | 6x6 | 100% | jev-latest | 20/20 | 0.892 | 0.600 | 0.200 |
| SimpleGrid | 6x6 | 100% | max-term | 20/20 | 0.531 | 0.496 | 0.200 |
| SimpleGrid | 6x6 | 100% | sharpsat-td | 20/20 | 0.250 | 0.313 | 0.200 |
| SimpleGrid | 6x6 | 100% | mc-sat | 7/20 | 0.429 | 0.401 | 0.200 |
| SimpleGrid | 6x6 | 100% | stop-rule | 20/20 | 1.000 | 1.000 | 0.200 |
| SimpleGrid | 7x7 | 25% | gpt-5.4-mini | 24/24 | 0.123 | 0.158 | 0.167 |
| SimpleGrid | 7x7 | 25% | gpt-6-luna | 24/24 | 0.116 | 0.169 | 0.167 |
| SimpleGrid | 7x7 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 24/24 | 0.282 | 0.191 | 0.167 |
| SimpleGrid | 7x7 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 24/24 | 0.156 | 0.169 | 0.167 |
| SimpleGrid | 7x7 | 25% | jev-latest | 24/24 | 0.201 | 0.171 | 0.167 |
| SimpleGrid | 7x7 | 25% | max-term | 24/24 | 0.172 | 0.171 | 0.167 |
| SimpleGrid | 7x7 | 25% | sharpsat-td | 23/24 | 0.109 | 0.171 | 0.167 |
| SimpleGrid | 7x7 | 25% | mc-sat | 0/24 | – | – | – |
| SimpleGrid | 7x7 | 25% | stop-rule | 24/24 | 0.167 | 0.167 | 0.167 |
| SimpleGrid | 7x7 | 100% | gpt-5.4-mini | 24/24 | 0.931 | 0.814 | 0.167 |
| SimpleGrid | 7x7 | 100% | gpt-6-luna | 24/24 | 0.926 | 0.690 | 0.167 |
| SimpleGrid | 7x7 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 24/24 | 0.625 | 0.490 | 0.167 |
| SimpleGrid | 7x7 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 24/24 | 0.324 | 0.236 | 0.167 |
| SimpleGrid | 7x7 | 100% | jev-latest | 24/24 | 0.896 | 0.536 | 0.167 |
| SimpleGrid | 7x7 | 100% | max-term | 24/24 | 0.602 | 0.542 | 0.167 |
| SimpleGrid | 7x7 | 100% | sharpsat-td | 7/24 | 0.143 | 0.179 | 0.167 |
| SimpleGrid | 7x7 | 100% | stop-rule | 24/24 | 1.000 | 1.000 | 0.167 |
| SimpleGrid | 8x8 | 25% | gpt-5.4-mini | 28/28 | 0.164 | 0.152 | 0.143 |
| SimpleGrid | 8x8 | 25% | gpt-6-luna | 28/28 | 0.166 | 0.158 | 0.143 |
| SimpleGrid | 8x8 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 28/28 | 0.158 | 0.150 | 0.143 |
| SimpleGrid | 8x8 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 28/28 | 0.110 | 0.139 | 0.143 |
| SimpleGrid | 8x8 | 25% | jev-latest | 28/28 | 0.153 | 0.148 | 0.143 |
| SimpleGrid | 8x8 | 25% | max-term | 28/28 | 0.149 | 0.147 | 0.143 |
| SimpleGrid | 8x8 | 25% | stop-rule | 28/28 | 0.143 | 0.143 | 0.143 |
| SimpleGrid | 8x8 | 100% | gpt-5.4-mini | 28/28 | 0.881 | 0.743 | 0.143 |
| SimpleGrid | 8x8 | 100% | gpt-6-luna | 28/28 | 0.908 | 0.594 | 0.143 |
| SimpleGrid | 8x8 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 28/28 | 0.509 | 0.427 | 0.143 |
| SimpleGrid | 8x8 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 28/28 | 0.264 | 0.186 | 0.143 |
| SimpleGrid | 8x8 | 100% | jev-latest | 28/28 | 0.679 | 0.476 | 0.143 |
| SimpleGrid | 8x8 | 100% | max-term | 28/28 | 0.436 | 0.421 | 0.143 |
| SimpleGrid | 8x8 | 100% | stop-rule | 28/28 | 1.000 | 1.000 | 0.143 |
| SimpleGrid | 9x9 | 25% | gpt-5.4-mini | 32/32 | 0.145 | 0.122 | 0.125 |
| SimpleGrid | 9x9 | 25% | gpt-6-luna | 32/32 | 0.179 | 0.155 | 0.125 |
| SimpleGrid | 9x9 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 32/32 | 0.127 | 0.131 | 0.125 |
| SimpleGrid | 9x9 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 32/32 | 0.127 | 0.111 | 0.125 |
| SimpleGrid | 9x9 | 25% | jev-latest | 32/32 | 0.194 | 0.127 | 0.125 |
| SimpleGrid | 9x9 | 25% | max-term | 32/32 | 0.133 | 0.132 | 0.125 |
| SimpleGrid | 9x9 | 25% | stop-rule | 32/32 | 0.125 | 0.125 | 0.125 |
| SimpleGrid | 9x9 | 100% | gpt-5.4-mini | 32/32 | 0.901 | 0.797 | 0.125 |
| SimpleGrid | 9x9 | 100% | gpt-6-luna | 32/32 | 0.929 | 0.654 | 0.125 |
| SimpleGrid | 9x9 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 32/32 | 0.486 | 0.358 | 0.125 |
| SimpleGrid | 9x9 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 32/32 | 0.113 | 0.129 | 0.125 |
| SimpleGrid | 9x9 | 100% | jev-latest | 32/32 | 0.889 | 0.546 | 0.125 |
| SimpleGrid | 9x9 | 100% | max-term | 32/32 | 0.510 | 0.478 | 0.125 |
| SimpleGrid | 9x9 | 100% | stop-rule | 32/32 | 1.000 | 1.000 | 0.125 |
| SimpleGrid | 10x10 | 25% | gpt-5.4-mini | 36/36 | 0.127 | 0.114 | 0.111 |
| SimpleGrid | 10x10 | 25% | gpt-6-luna | 36/36 | 0.081 | 0.114 | 0.111 |
| SimpleGrid | 10x10 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 36/36 | 0.123 | 0.107 | 0.111 |
| SimpleGrid | 10x10 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 36/36 | 0.084 | 0.106 | 0.111 |
| SimpleGrid | 10x10 | 25% | jev-latest | 36/36 | 0.128 | 0.116 | 0.111 |
| SimpleGrid | 10x10 | 25% | max-term | 36/36 | 0.119 | 0.118 | 0.111 |
| SimpleGrid | 10x10 | 25% | stop-rule | 36/36 | 0.111 | 0.111 | 0.111 |
| SimpleGrid | 10x10 | 100% | gpt-5.4-mini | 36/36 | 0.873 | 0.746 | 0.111 |
| SimpleGrid | 10x10 | 100% | gpt-6-luna | 36/36 | 0.742 | 0.575 | 0.111 |
| SimpleGrid | 10x10 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 36/36 | 0.474 | 0.350 | 0.111 |
| SimpleGrid | 10x10 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 36/36 | 0.155 | 0.126 | 0.111 |
| SimpleGrid | 10x10 | 100% | jev-latest | 36/36 | 0.810 | 0.435 | 0.111 |
| SimpleGrid | 10x10 | 100% | max-term | 36/36 | 0.499 | 0.433 | 0.111 |
| SimpleGrid | 10x10 | 100% | stop-rule | 36/36 | 1.000 | 1.000 | 0.111 |
| TwoPackage | 3x3 | 25% | gpt-5.4-mini | 16/16 | 0.312 | 0.309 | 0.250 |
| TwoPackage | 3x3 | 25% | gpt-6-luna | 16/16 | 0.458 | 0.458 | 0.250 |
| TwoPackage | 3x3 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.240 | 0.258 | 0.250 |
| TwoPackage | 3x3 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.307 | 0.281 | 0.250 |
| TwoPackage | 3x3 | 25% | jev-latest | 16/16 | 0.344 | 0.317 | 0.250 |
| TwoPackage | 3x3 | 25% | max-term | 16/16 | 0.500 | 0.468 | 0.250 |
| TwoPackage | 3x3 | 25% | sharpsat-td | 16/16 | 0.375 | 0.484 | 0.250 |
| TwoPackage | 3x3 | 25% | mc-sat | 7/16 | 0.429 | 0.446 | 0.250 |
| TwoPackage | 3x3 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| TwoPackage | 3x3 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.891 | 0.250 |
| TwoPackage | 3x3 | 100% | gpt-6-luna | 16/16 | 1.000 | 0.996 | 0.250 |
| TwoPackage | 3x3 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.781 | 0.689 | 0.250 |
| TwoPackage | 3x3 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.250 | 0.248 | 0.250 |
| TwoPackage | 3x3 | 100% | jev-latest | 16/16 | 1.000 | 0.896 | 0.250 |
| TwoPackage | 3x3 | 100% | max-term | 16/16 | 1.000 | 0.976 | 0.250 |
| TwoPackage | 3x3 | 100% | sharpsat-td | 16/16 | 1.000 | 0.998 | 0.250 |
| TwoPackage | 3x3 | 100% | mc-sat | 10/16 | 1.000 | 0.992 | 0.250 |
| TwoPackage | 3x3 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| TwoPackage | 4x4 | 25% | gpt-5.4-mini | 16/16 | 0.490 | 0.365 | 0.250 |
| TwoPackage | 4x4 | 25% | gpt-6-luna | 16/16 | 0.458 | 0.428 | 0.250 |
| TwoPackage | 4x4 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.328 | 0.281 | 0.250 |
| TwoPackage | 4x4 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.294 | 0.264 | 0.250 |
| TwoPackage | 4x4 | 25% | jev-latest | 16/16 | 0.458 | 0.332 | 0.250 |
| TwoPackage | 4x4 | 25% | max-term | 16/16 | 0.438 | 0.405 | 0.250 |
| TwoPackage | 4x4 | 25% | sharpsat-td | 0/16 | – | – | – |
| TwoPackage | 4x4 | 25% | mc-sat | 0/16 | – | – | – |
| TwoPackage | 4x4 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| TwoPackage | 4x4 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.916 | 0.250 |
| TwoPackage | 4x4 | 100% | gpt-6-luna | 16/16 | 1.000 | 0.994 | 0.250 |
| TwoPackage | 4x4 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.625 | 0.544 | 0.250 |
| TwoPackage | 4x4 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.302 | 0.250 | 0.250 |
| TwoPackage | 4x4 | 100% | jev-latest | 16/16 | 1.000 | 0.896 | 0.250 |
| TwoPackage | 4x4 | 100% | max-term | 16/16 | 1.000 | 0.981 | 0.250 |
| TwoPackage | 4x4 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| TwoPackage | 5x5 | 25% | gpt-5.4-mini | 16/16 | 0.302 | 0.298 | 0.250 |
| TwoPackage | 5x5 | 25% | gpt-6-luna | 16/16 | 0.470 | 0.460 | 0.250 |
| TwoPackage | 5x5 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.281 | 0.257 | 0.250 |
| TwoPackage | 5x5 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.271 | 0.258 | 0.250 |
| TwoPackage | 5x5 | 25% | jev-latest | 16/16 | 0.375 | 0.289 | 0.250 |
| TwoPackage | 5x5 | 25% | max-term | 16/16 | 0.422 | 0.393 | 0.250 |
| TwoPackage | 5x5 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| TwoPackage | 5x5 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.938 | 0.250 |
| TwoPackage | 5x5 | 100% | gpt-6-luna | 16/16 | 1.000 | 0.996 | 0.250 |
| TwoPackage | 5x5 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.776 | 0.641 | 0.250 |
| TwoPackage | 5x5 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.325 | 0.273 | 0.250 |
| TwoPackage | 5x5 | 100% | jev-latest | 16/16 | 1.000 | 0.937 | 0.250 |
| TwoPackage | 5x5 | 100% | max-term | 16/16 | 1.000 | 0.984 | 0.250 |
| TwoPackage | 5x5 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| TwoPackage | 6x6 | 25% | gpt-5.4-mini | 16/16 | 0.469 | 0.349 | 0.250 |
| TwoPackage | 6x6 | 25% | gpt-6-luna | 16/16 | 0.354 | 0.384 | 0.250 |
| TwoPackage | 6x6 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.281 | 0.254 | 0.250 |
| TwoPackage | 6x6 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.163 | 0.230 | 0.250 |
| TwoPackage | 6x6 | 25% | jev-latest | 16/16 | 0.417 | 0.323 | 0.250 |
| TwoPackage | 6x6 | 25% | max-term | 16/16 | 0.406 | 0.393 | 0.250 |
| TwoPackage | 6x6 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| TwoPackage | 6x6 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.938 | 0.250 |
| TwoPackage | 6x6 | 100% | gpt-6-luna | 16/16 | 1.000 | 0.999 | 0.250 |
| TwoPackage | 6x6 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.854 | 0.688 | 0.250 |
| TwoPackage | 6x6 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.424 | 0.335 | 0.250 |
| TwoPackage | 6x6 | 100% | jev-latest | 16/16 | 1.000 | 0.905 | 0.250 |
| TwoPackage | 6x6 | 100% | max-term | 16/16 | 1.000 | 0.993 | 0.250 |
| TwoPackage | 6x6 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| TwoPackage | 7x7 | 25% | gpt-5.4-mini | 16/16 | 0.198 | 0.255 | 0.250 |
| TwoPackage | 7x7 | 25% | gpt-6-luna | 16/16 | 0.448 | 0.446 | 0.250 |
| TwoPackage | 7x7 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.245 | 0.245 | 0.250 |
| TwoPackage | 7x7 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.229 | 0.266 | 0.250 |
| TwoPackage | 7x7 | 25% | jev-latest | 16/16 | 0.292 | 0.287 | 0.250 |
| TwoPackage | 7x7 | 25% | max-term | 16/16 | 0.453 | 0.426 | 0.250 |
| TwoPackage | 7x7 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| TwoPackage | 7x7 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.949 | 0.250 |
| TwoPackage | 7x7 | 100% | gpt-6-luna | 16/16 | 1.000 | 0.999 | 0.250 |
| TwoPackage | 7x7 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.823 | 0.694 | 0.250 |
| TwoPackage | 7x7 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.340 | 0.300 | 0.250 |
| TwoPackage | 7x7 | 100% | jev-latest | 16/16 | 1.000 | 0.935 | 0.250 |
| TwoPackage | 7x7 | 100% | max-term | 16/16 | 1.000 | 0.976 | 0.250 |
| TwoPackage | 7x7 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| TwoPackageOneway | 3x3 | 25% | gpt-5.4-mini | 16/16 | 0.385 | 0.344 | 0.250 |
| TwoPackageOneway | 3x3 | 25% | gpt-6-luna | 16/16 | 0.453 | 0.474 | 0.250 |
| TwoPackageOneway | 3x3 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.281 | 0.302 | 0.250 |
| TwoPackageOneway | 3x3 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.335 | 0.277 | 0.250 |
| TwoPackageOneway | 3x3 | 25% | jev-latest | 16/16 | 0.417 | 0.322 | 0.250 |
| TwoPackageOneway | 3x3 | 25% | max-term | 16/16 | 0.500 | 0.469 | 0.250 |
| TwoPackageOneway | 3x3 | 25% | sharpsat-td | 16/16 | 0.375 | 0.480 | 0.250 |
| TwoPackageOneway | 3x3 | 25% | mc-sat | 8/16 | 0.250 | 0.327 | 0.250 |
| TwoPackageOneway | 3x3 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| TwoPackageOneway | 3x3 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.901 | 0.250 |
| TwoPackageOneway | 3x3 | 100% | gpt-6-luna | 16/16 | 1.000 | 0.992 | 0.250 |
| TwoPackageOneway | 3x3 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.677 | 0.613 | 0.250 |
| TwoPackageOneway | 3x3 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.314 | 0.310 | 0.250 |
| TwoPackageOneway | 3x3 | 100% | jev-latest | 16/16 | 1.000 | 0.902 | 0.250 |
| TwoPackageOneway | 3x3 | 100% | max-term | 16/16 | 1.000 | 0.988 | 0.250 |
| TwoPackageOneway | 3x3 | 100% | sharpsat-td | 16/16 | 1.000 | 0.998 | 0.250 |
| TwoPackageOneway | 3x3 | 100% | mc-sat | 11/16 | 1.000 | 0.995 | 0.250 |
| TwoPackageOneway | 3x3 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| TwoPackageOneway | 4x4 | 25% | gpt-5.4-mini | 16/16 | 0.396 | 0.314 | 0.250 |
| TwoPackageOneway | 4x4 | 25% | gpt-6-luna | 16/16 | 0.448 | 0.442 | 0.250 |
| TwoPackageOneway | 4x4 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.297 | 0.287 | 0.250 |
| TwoPackageOneway | 4x4 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.394 | 0.282 | 0.250 |
| TwoPackageOneway | 4x4 | 25% | jev-latest | 16/16 | 0.479 | 0.329 | 0.250 |
| TwoPackageOneway | 4x4 | 25% | max-term | 16/16 | 0.438 | 0.408 | 0.250 |
| TwoPackageOneway | 4x4 | 25% | sharpsat-td | 4/16 | 0.500 | 0.512 | 0.250 |
| TwoPackageOneway | 4x4 | 25% | mc-sat | 7/16 | 0.286 | 0.299 | 0.250 |
| TwoPackageOneway | 4x4 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| TwoPackageOneway | 4x4 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.917 | 0.250 |
| TwoPackageOneway | 4x4 | 100% | gpt-6-luna | 16/16 | 1.000 | 0.997 | 0.250 |
| TwoPackageOneway | 4x4 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.766 | 0.646 | 0.250 |
| TwoPackageOneway | 4x4 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.372 | 0.296 | 0.250 |
| TwoPackageOneway | 4x4 | 100% | jev-latest | 16/16 | 1.000 | 0.912 | 0.250 |
| TwoPackageOneway | 4x4 | 100% | max-term | 16/16 | 1.000 | 0.981 | 0.250 |
| TwoPackageOneway | 4x4 | 100% | mc-sat | 5/16 | 1.000 | 1.000 | 0.250 |
| TwoPackageOneway | 4x4 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| TwoPackageOneway | 5x5 | 25% | gpt-5.4-mini | 16/16 | 0.365 | 0.312 | 0.250 |
| TwoPackageOneway | 5x5 | 25% | gpt-6-luna | 16/16 | 0.521 | 0.489 | 0.250 |
| TwoPackageOneway | 5x5 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.247 | 0.269 | 0.250 |
| TwoPackageOneway | 5x5 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.309 | 0.277 | 0.250 |
| TwoPackageOneway | 5x5 | 25% | jev-latest | 16/16 | 0.417 | 0.314 | 0.250 |
| TwoPackageOneway | 5x5 | 25% | max-term | 16/16 | 0.500 | 0.475 | 0.250 |
| TwoPackageOneway | 5x5 | 25% | mc-sat | 2/16 | 0.000 | 0.166 | 0.250 |
| TwoPackageOneway | 5x5 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| TwoPackageOneway | 5x5 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.950 | 0.250 |
| TwoPackageOneway | 5x5 | 100% | gpt-6-luna | 16/16 | 1.000 | 0.998 | 0.250 |
| TwoPackageOneway | 5x5 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.786 | 0.657 | 0.250 |
| TwoPackageOneway | 5x5 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.276 | 0.299 | 0.250 |
| TwoPackageOneway | 5x5 | 100% | jev-latest | 16/16 | 1.000 | 0.934 | 0.250 |
| TwoPackageOneway | 5x5 | 100% | max-term | 16/16 | 1.000 | 0.984 | 0.250 |
| TwoPackageOneway | 5x5 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| TwoPackageOneway | 6x6 | 25% | gpt-5.4-mini | 16/16 | 0.271 | 0.295 | 0.250 |
| TwoPackageOneway | 6x6 | 25% | gpt-6-luna | 16/16 | 0.323 | 0.351 | 0.250 |
| TwoPackageOneway | 6x6 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.417 | 0.326 | 0.250 |
| TwoPackageOneway | 6x6 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.250 | 0.265 | 0.250 |
| TwoPackageOneway | 6x6 | 25% | jev-latest | 16/16 | 0.365 | 0.301 | 0.250 |
| TwoPackageOneway | 6x6 | 25% | max-term | 16/16 | 0.391 | 0.383 | 0.250 |
| TwoPackageOneway | 6x6 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| TwoPackageOneway | 6x6 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.926 | 0.250 |
| TwoPackageOneway | 6x6 | 100% | gpt-6-luna | 16/16 | 1.000 | 0.998 | 0.250 |
| TwoPackageOneway | 6x6 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.719 | 0.618 | 0.250 |
| TwoPackageOneway | 6x6 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.413 | 0.296 | 0.250 |
| TwoPackageOneway | 6x6 | 100% | jev-latest | 16/16 | 1.000 | 0.912 | 0.250 |
| TwoPackageOneway | 6x6 | 100% | max-term | 16/16 | 1.000 | 0.983 | 0.250 |
| TwoPackageOneway | 6x6 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| TwoPackageOneway | 7x7 | 25% | gpt-5.4-mini | 16/16 | 0.281 | 0.293 | 0.250 |
| TwoPackageOneway | 7x7 | 25% | gpt-6-luna | 16/16 | 0.328 | 0.332 | 0.250 |
| TwoPackageOneway | 7x7 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.323 | 0.300 | 0.250 |
| TwoPackageOneway | 7x7 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.271 | 0.254 | 0.250 |
| TwoPackageOneway | 7x7 | 25% | jev-latest | 16/16 | 0.312 | 0.286 | 0.250 |
| TwoPackageOneway | 7x7 | 25% | max-term | 16/16 | 0.406 | 0.392 | 0.250 |
| TwoPackageOneway | 7x7 | 25% | stop-rule | 16/16 | 0.250 | 0.250 | 0.250 |
| TwoPackageOneway | 7x7 | 100% | gpt-5.4-mini | 16/16 | 1.000 | 0.947 | 0.250 |
| TwoPackageOneway | 7x7 | 100% | gpt-6-luna | 16/16 | 1.000 | 0.999 | 0.250 |
| TwoPackageOneway | 7x7 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 16/16 | 0.750 | 0.648 | 0.250 |
| TwoPackageOneway | 7x7 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 16/16 | 0.340 | 0.307 | 0.250 |
| TwoPackageOneway | 7x7 | 100% | jev-latest | 16/16 | 1.000 | 0.939 | 0.250 |
| TwoPackageOneway | 7x7 | 100% | max-term | 16/16 | 1.000 | 0.985 | 0.250 |
| TwoPackageOneway | 7x7 | 100% | stop-rule | 16/16 | 1.000 | 1.000 | 0.250 |
| ThreePackage | 5x5 | 25% | gpt-5.4-mini | 32/32 | 0.138 | 0.138 | 0.125 |
| ThreePackage | 5x5 | 25% | gpt-6-luna | 32/32 | 0.128 | 0.132 | 0.125 |
| ThreePackage | 5x5 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 32/32 | 0.103 | 0.129 | 0.125 |
| ThreePackage | 5x5 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 32/32 | 0.117 | 0.132 | 0.125 |
| ThreePackage | 5x5 | 25% | jev-latest | 32/32 | 0.156 | 0.134 | 0.125 |
| ThreePackage | 5x5 | 25% | stop-rule | 32/32 | 0.125 | 0.125 | 0.125 |
| ThreePackage | 5x5 | 100% | gpt-5.4-mini | 32/32 | 0.851 | 0.832 | 0.125 |
| ThreePackage | 5x5 | 100% | gpt-6-luna | 32/32 | 1.000 | 0.998 | 0.125 |
| ThreePackage | 5x5 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 32/32 | 0.253 | 0.220 | 0.125 |
| ThreePackage | 5x5 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 32/32 | 0.126 | 0.112 | 0.125 |
| ThreePackage | 5x5 | 100% | jev-latest | 32/32 | 1.000 | 0.927 | 0.125 |
| ThreePackage | 5x5 | 100% | stop-rule | 32/32 | 1.000 | 1.000 | 0.125 |
| ThreePackage | 6x6 | 25% | gpt-5.4-mini | 8/8 | 0.201 | 0.170 | 0.125 |
| ThreePackage | 6x6 | 25% | gpt-6-luna | 8/8 | 0.229 | 0.197 | 0.125 |
| ThreePackage | 6x6 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 8/8 | 0.219 | 0.159 | 0.125 |
| ThreePackage | 6x6 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 8/8 | 0.250 | 0.138 | 0.125 |
| ThreePackage | 6x6 | 25% | jev-latest | 8/8 | 0.271 | 0.180 | 0.125 |
| ThreePackage | 6x6 | 25% | stop-rule | 8/8 | 0.125 | 0.125 | 0.125 |
| ThreePackage | 6x6 | 100% | gpt-5.4-mini | 8/8 | 0.875 | 0.776 | 0.125 |
| ThreePackage | 6x6 | 100% | gpt-6-luna | 8/8 | 1.000 | 0.998 | 0.125 |
| ThreePackage | 6x6 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 8/8 | 0.396 | 0.317 | 0.125 |
| ThreePackage | 6x6 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 8/8 | 0.146 | 0.144 | 0.125 |
| ThreePackage | 6x6 | 100% | jev-latest | 8/8 | 1.000 | 0.897 | 0.125 |
| ThreePackage | 6x6 | 100% | stop-rule | 8/8 | 1.000 | 1.000 | 0.125 |
| FourPackage | 6x6 | 25% | gpt-5.4-mini | 48/48 | 0.171 | 0.129 | 0.083 |
| FourPackage | 6x6 | 25% | gpt-6-luna | 48/48 | 0.305 | 0.298 | 0.083 |
| FourPackage | 6x6 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 48/48 | 0.124 | 0.107 | 0.083 |
| FourPackage | 6x6 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 48/48 | 0.093 | 0.085 | 0.083 |
| FourPackage | 6x6 | 25% | jev-latest | 48/48 | 0.307 | 0.180 | 0.083 |
| FourPackage | 6x6 | 25% | max-term | 0/48 | – | – | – |
| FourPackage | 6x6 | 25% | stop-rule | 48/48 | 0.083 | 0.083 | 0.083 |
| FourPackage | 6x6 | 100% | gpt-5.4-mini | 48/48 | 0.979 | 0.880 | 0.083 |
| FourPackage | 6x6 | 100% | gpt-6-luna | 48/48 | 1.000 | 0.994 | 0.083 |
| FourPackage | 6x6 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 48/48 | 0.493 | 0.383 | 0.083 |
| FourPackage | 6x6 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 48/48 | 0.093 | 0.087 | 0.083 |
| FourPackage | 6x6 | 100% | jev-latest | 48/48 | 1.000 | 0.930 | 0.083 |
| FourPackage | 6x6 | 100% | stop-rule | 48/48 | 1.000 | 1.000 | 0.083 |
| FourPackage | 7x7 | 25% | gpt-5.4-mini | 48/48 | 0.179 | 0.132 | 0.083 |
| FourPackage | 7x7 | 25% | gpt-6-luna | 48/48 | 0.280 | 0.235 | 0.083 |
| FourPackage | 7x7 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 48/48 | 0.113 | 0.089 | 0.083 |
| FourPackage | 7x7 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 48/48 | 0.079 | 0.084 | 0.083 |
| FourPackage | 7x7 | 25% | jev-latest | 48/48 | 0.208 | 0.139 | 0.083 |
| FourPackage | 7x7 | 25% | stop-rule | 48/48 | 0.083 | 0.083 | 0.083 |
| FourPackage | 7x7 | 100% | gpt-5.4-mini | 48/48 | 0.979 | 0.897 | 0.083 |
| FourPackage | 7x7 | 100% | gpt-6-luna | 48/48 | 1.000 | 0.996 | 0.083 |
| FourPackage | 7x7 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 48/48 | 0.520 | 0.397 | 0.083 |
| FourPackage | 7x7 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 48/48 | 0.137 | 0.108 | 0.083 |
| FourPackage | 7x7 | 100% | jev-latest | 48/48 | 1.000 | 0.936 | 0.083 |
| FourPackage | 7x7 | 100% | stop-rule | 48/48 | 1.000 | 1.000 | 0.083 |
| FourPackage | 8x8 | 25% | gpt-5.4-mini | 48/48 | 0.183 | 0.128 | 0.083 |
| FourPackage | 8x8 | 25% | gpt-6-luna | 48/48 | 0.315 | 0.275 | 0.083 |
| FourPackage | 8x8 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 48/48 | 0.087 | 0.096 | 0.083 |
| FourPackage | 8x8 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 48/48 | 0.118 | 0.081 | 0.083 |
| FourPackage | 8x8 | 25% | jev-latest | 48/48 | 0.177 | 0.152 | 0.083 |
| FourPackage | 8x8 | 25% | stop-rule | 48/48 | 0.083 | 0.083 | 0.083 |
| FourPackage | 8x8 | 100% | gpt-5.4-mini | 48/48 | 1.000 | 0.926 | 0.083 |
| FourPackage | 8x8 | 100% | gpt-6-luna | 48/48 | 1.000 | 0.997 | 0.083 |
| FourPackage | 8x8 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 48/48 | 0.499 | 0.413 | 0.083 |
| FourPackage | 8x8 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 48/48 | 0.109 | 0.083 | 0.083 |
| FourPackage | 8x8 | 100% | jev-latest | 48/48 | 1.000 | 0.950 | 0.083 |
| FourPackage | 8x8 | 100% | stop-rule | 48/48 | 1.000 | 1.000 | 0.083 |
| FourPackage | 9x9 | 25% | gpt-5.4-mini | 24/24 | 0.134 | 0.139 | 0.083 |
| FourPackage | 9x9 | 25% | gpt-6-luna | 24/24 | 0.306 | 0.303 | 0.083 |
| FourPackage | 9x9 | 25% | hf:Qwen/Qwen2.5-7B-Instruct | 24/24 | 0.135 | 0.099 | 0.083 |
| FourPackage | 9x9 | 25% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 24/24 | 0.087 | 0.092 | 0.083 |
| FourPackage | 9x9 | 25% | jev-latest | 24/24 | 0.299 | 0.192 | 0.083 |
| FourPackage | 9x9 | 25% | stop-rule | 24/24 | 0.083 | 0.083 | 0.083 |
| FourPackage | 9x9 | 100% | gpt-5.4-mini | 24/24 | 1.000 | 0.930 | 0.083 |
| FourPackage | 9x9 | 100% | gpt-6-luna | 24/24 | 1.000 | 0.997 | 0.083 |
| FourPackage | 9x9 | 100% | hf:Qwen/Qwen2.5-7B-Instruct | 24/24 | 0.479 | 0.392 | 0.083 |
| FourPackage | 9x9 | 100% | hf:meta-llama/Meta-Llama-3-8B-Instruct | 24/24 | 0.090 | 0.096 | 0.083 |
| FourPackage | 9x9 | 100% | jev-latest | 24/24 | 1.000 | 0.937 | 0.083 |
| FourPackage | 9x9 | 100% | stop-rule | 24/24 | 1.000 | 1.000 | 0.083 |

## Same-file comparison with the recognizers and the stop rule

LLM minus reference, on files both answered. Intervals are 95%, from resampling problems.

| LLM | reference | family | evidence | files | LLM acc | ref acc | acc diff | LLM P(true) | ref P(true) | P(true) diff |
|---|---|---|---|---|---|---|---|---|---|---|
| gpt-5.4-mini | max-term | SimpleGrid | 25% | 176 | 0.184 | 0.187 | -0.003 [-0.024, +0.016] | 0.182 | 0.186 | -0.004 [-0.009, +0.001] |
| gpt-5.4-mini | max-term | SimpleGrid | 100% | 176 | 0.924 | 0.545 | +0.379 [+0.353, +0.403] | 0.800 | 0.510 | +0.290 [+0.267, +0.308] |
| gpt-5.4-mini | max-term | TwoPackage | 25% | 80 | 0.354 | 0.444 | -0.090 [-0.164, -0.016] | 0.315 | 0.417 | -0.102 [-0.136, -0.067] |
| gpt-5.4-mini | max-term | TwoPackage | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.927 | 0.982 | -0.055 [-0.068, -0.043] |
| gpt-5.4-mini | max-term | TwoPackageOneway | 25% | 80 | 0.340 | 0.447 | -0.107 [-0.165, -0.051] | 0.312 | 0.425 | -0.113 [-0.142, -0.085] |
| gpt-5.4-mini | max-term | TwoPackageOneway | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.928 | 0.984 | -0.056 [-0.073, -0.042] |
| gpt-5.4-mini | sharpsat-td | SimpleGrid | 25% | 79 | 0.233 | 0.304 | -0.071 [-0.136, -0.001] | 0.248 | 0.278 | -0.030 [-0.046, -0.014] |
| gpt-5.4-mini | sharpsat-td | SimpleGrid | 100% | 63 | 0.979 | 0.317 | +0.661 [+0.608, +0.711] | 0.843 | 0.422 | +0.421 [+0.368, +0.469] |
| gpt-5.4-mini | sharpsat-td | TwoPackage | 25% | 16 | 0.312 | 0.375 | -0.062 [-0.250, +0.125] | 0.309 | 0.484 | -0.176 [-0.230, -0.121] |
| gpt-5.4-mini | sharpsat-td | TwoPackage | 100% | 16 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.891 | 0.998 | -0.106 [-0.131, -0.088] |
| gpt-5.4-mini | sharpsat-td | TwoPackageOneway | 25% | 20 | 0.442 | 0.400 | +0.042 [-0.142, +0.217] | 0.348 | 0.487 | -0.138 [-0.209, -0.070] |
| gpt-5.4-mini | sharpsat-td | TwoPackageOneway | 100% | 16 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.901 | 0.998 | -0.098 [-0.124, -0.076] |
| gpt-5.4-mini | mc-sat | SimpleGrid | 25% | 41 | 0.308 | 0.366 | -0.058 [-0.189, +0.084] | 0.312 | 0.343 | -0.031 [-0.075, +0.010] |
| gpt-5.4-mini | mc-sat | SimpleGrid | 100% | 39 | 0.991 | 0.564 | +0.427 [+0.316, +0.550] | 0.881 | 0.621 | +0.260 [+0.191, +0.344] |
| gpt-5.4-mini | mc-sat | TwoPackage | 25% | 7 | 0.333 | 0.429 | -0.095 [-0.233, +0.250] | 0.320 | 0.446 | -0.125 [-0.217, -0.056] |
| gpt-5.4-mini | mc-sat | TwoPackage | 100% | 10 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.857 | 0.992 | -0.135 [-0.165, -0.114] |
| gpt-5.4-mini | mc-sat | TwoPackageOneway | 25% | 17 | 0.461 | 0.235 | +0.225 [-0.083, +0.456] | 0.365 | 0.296 | +0.069 [-0.076, +0.185] |
| gpt-5.4-mini | mc-sat | TwoPackageOneway | 100% | 16 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.869 | 0.996 | -0.127 [-0.174, -0.096] |
| gpt-5.4-mini | stop-rule | SimpleGrid | 25% | 176 | 0.184 | 0.182 | +0.002 [-0.020, +0.021] | 0.182 | 0.182 | +0.000 [-0.005, +0.005] |
| gpt-5.4-mini | stop-rule | SimpleGrid | 100% | 176 | 0.924 | 1.000 | -0.076 [-0.097, -0.053] | 0.800 | 1.000 | -0.200 [-0.220, -0.176] |
| gpt-5.4-mini | stop-rule | TwoPackage | 25% | 80 | 0.354 | 0.250 | +0.104 [+0.033, +0.181] | 0.315 | 0.250 | +0.065 [+0.037, +0.096] |
| gpt-5.4-mini | stop-rule | TwoPackage | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.927 | 1.000 | -0.073 [-0.087, -0.060] |
| gpt-5.4-mini | stop-rule | TwoPackageOneway | 25% | 80 | 0.340 | 0.250 | +0.090 [+0.031, +0.154] | 0.312 | 0.250 | +0.062 [+0.037, +0.087] |
| gpt-5.4-mini | stop-rule | TwoPackageOneway | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.928 | 1.000 | -0.072 [-0.085, -0.060] |
| gpt-5.4-mini | stop-rule | ThreePackage | 25% | 40 | 0.151 | 0.125 | +0.026 [-0.013, +0.065] | 0.144 | 0.125 | +0.019 [+0.004, +0.037] |
| gpt-5.4-mini | stop-rule | ThreePackage | 100% | 40 | 0.856 | 1.000 | -0.144 [-0.182, -0.117] | 0.821 | 1.000 | -0.179 [-0.226, -0.135] |
| gpt-5.4-mini | stop-rule | FourPackage | 25% | 168 | 0.172 | 0.083 | +0.088 [+0.051, +0.129] | 0.131 | 0.083 | +0.048 [+0.030, +0.070] |
| gpt-5.4-mini | stop-rule | FourPackage | 100% | 168 | 0.988 | 1.000 | -0.012 [-0.022, -0.004] | 0.905 | 1.000 | -0.095 [-0.108, -0.081] |
| gpt-6-luna | max-term | SimpleGrid | 25% | 176 | 0.203 | 0.187 | +0.016 [-0.018, +0.056] | 0.198 | 0.186 | +0.012 [+0.003, +0.022] |
| gpt-6-luna | max-term | SimpleGrid | 100% | 176 | 0.884 | 0.545 | +0.340 [+0.299, +0.377] | 0.655 | 0.510 | +0.145 [+0.128, +0.161] |
| gpt-6-luna | max-term | TwoPackage | 25% | 80 | 0.438 | 0.444 | -0.006 [-0.043, +0.032] | 0.435 | 0.417 | +0.018 [-0.007, +0.041] |
| gpt-6-luna | max-term | TwoPackage | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.997 | 0.982 | +0.015 [+0.007, +0.023] |
| gpt-6-luna | max-term | TwoPackageOneway | 25% | 80 | 0.415 | 0.447 | -0.032 [-0.067, +0.005] | 0.418 | 0.425 | -0.008 [-0.032, +0.020] |
| gpt-6-luna | max-term | TwoPackageOneway | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.997 | 0.984 | +0.012 [+0.005, +0.021] |
| gpt-6-luna | sharpsat-td | SimpleGrid | 25% | 79 | 0.285 | 0.304 | -0.019 [-0.061, +0.030] | 0.268 | 0.278 | -0.010 [-0.019, -0.002] |
| gpt-6-luna | sharpsat-td | SimpleGrid | 100% | 63 | 0.921 | 0.317 | +0.604 [+0.549, +0.660] | 0.707 | 0.422 | +0.285 [+0.244, +0.324] |
| gpt-6-luna | sharpsat-td | TwoPackage | 25% | 16 | 0.458 | 0.375 | +0.083 [-0.104, +0.271] | 0.458 | 0.484 | -0.026 [-0.111, +0.045] |
| gpt-6-luna | sharpsat-td | TwoPackage | 100% | 16 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.996 | 0.998 | -0.001 [-0.004, +0.000] |
| gpt-6-luna | sharpsat-td | TwoPackageOneway | 25% | 20 | 0.454 | 0.400 | +0.054 [-0.037, +0.150] | 0.470 | 0.487 | -0.017 [-0.041, +0.010] |
| gpt-6-luna | sharpsat-td | TwoPackageOneway | 100% | 16 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.992 | 0.998 | -0.006 [-0.017, +0.000] |
| gpt-6-luna | mc-sat | SimpleGrid | 25% | 41 | 0.397 | 0.366 | +0.031 [-0.090, +0.149] | 0.334 | 0.343 | -0.009 [-0.048, +0.025] |
| gpt-6-luna | mc-sat | SimpleGrid | 100% | 39 | 0.934 | 0.564 | +0.370 [+0.249, +0.505] | 0.758 | 0.621 | +0.137 [+0.086, +0.196] |
| gpt-6-luna | mc-sat | TwoPackage | 25% | 7 | 0.381 | 0.429 | -0.048 [-0.318, +0.500] | 0.376 | 0.446 | -0.070 [-0.120, -0.006] |
| gpt-6-luna | mc-sat | TwoPackage | 100% | 10 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.994 | 0.992 | +0.002 [+0.000, +0.005] |
| gpt-6-luna | mc-sat | TwoPackageOneway | 25% | 17 | 0.402 | 0.235 | +0.167 [-0.173, +0.436] | 0.415 | 0.296 | +0.119 [-0.070, +0.277] |
| gpt-6-luna | mc-sat | TwoPackageOneway | 100% | 16 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.991 | 0.996 | -0.006 [-0.013, -0.001] |
| gpt-6-luna | stop-rule | SimpleGrid | 25% | 176 | 0.203 | 0.182 | +0.022 [-0.013, +0.060] | 0.198 | 0.182 | +0.016 [+0.007, +0.025] |
| gpt-6-luna | stop-rule | SimpleGrid | 100% | 176 | 0.884 | 1.000 | -0.116 [-0.153, -0.079] | 0.655 | 1.000 | -0.345 [-0.371, -0.314] |
| gpt-6-luna | stop-rule | TwoPackage | 25% | 80 | 0.438 | 0.250 | +0.188 [+0.136, +0.233] | 0.435 | 0.250 | +0.185 [+0.143, +0.222] |
| gpt-6-luna | stop-rule | TwoPackage | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.997 | 1.000 | -0.003 [-0.006, -0.001] |
| gpt-6-luna | stop-rule | TwoPackageOneway | 25% | 80 | 0.415 | 0.250 | +0.165 [+0.106, +0.218] | 0.418 | 0.250 | +0.168 [+0.123, +0.208] |
| gpt-6-luna | stop-rule | TwoPackageOneway | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.997 | 1.000 | -0.003 [-0.006, -0.001] |
| gpt-6-luna | stop-rule | ThreePackage | 25% | 40 | 0.148 | 0.125 | +0.023 [-0.008, +0.064] | 0.145 | 0.125 | +0.020 [-0.007, +0.051] |
| gpt-6-luna | stop-rule | ThreePackage | 100% | 40 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.998 | 1.000 | -0.002 [-0.004, +0.000] |
| gpt-6-luna | stop-rule | FourPackage | 25% | 168 | 0.301 | 0.083 | +0.217 [+0.187, +0.253] | 0.274 | 0.083 | +0.191 [+0.162, +0.221] |
| gpt-6-luna | stop-rule | FourPackage | 100% | 168 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.996 | 1.000 | -0.004 [-0.005, -0.003] |
| hf:Qwen/Qwen2.5-7B-Instruct | max-term | SimpleGrid | 25% | 176 | 0.207 | 0.187 | +0.020 [-0.014, +0.056] | 0.188 | 0.186 | +0.002 [-0.013, +0.017] |
| hf:Qwen/Qwen2.5-7B-Instruct | max-term | SimpleGrid | 100% | 176 | 0.596 | 0.545 | +0.051 [+0.001, +0.104] | 0.474 | 0.510 | -0.036 [-0.070, +0.004] |
| hf:Qwen/Qwen2.5-7B-Instruct | max-term | TwoPackage | 25% | 80 | 0.275 | 0.444 | -0.169 [-0.222, -0.109] | 0.259 | 0.417 | -0.158 [-0.191, -0.119] |
| hf:Qwen/Qwen2.5-7B-Instruct | max-term | TwoPackage | 100% | 80 | 0.772 | 1.000 | -0.228 [-0.303, -0.167] | 0.651 | 0.982 | -0.331 [-0.388, -0.283] |
| hf:Qwen/Qwen2.5-7B-Instruct | max-term | TwoPackageOneway | 25% | 80 | 0.313 | 0.447 | -0.134 [-0.199, -0.067] | 0.297 | 0.425 | -0.129 [-0.171, -0.088] |
| hf:Qwen/Qwen2.5-7B-Instruct | max-term | TwoPackageOneway | 100% | 80 | 0.740 | 1.000 | -0.260 [-0.307, -0.217] | 0.636 | 0.984 | -0.348 [-0.386, -0.311] |
| hf:Qwen/Qwen2.5-7B-Instruct | sharpsat-td | SimpleGrid | 25% | 79 | 0.290 | 0.304 | -0.014 [-0.097, +0.072] | 0.260 | 0.278 | -0.018 [-0.044, +0.009] |
| hf:Qwen/Qwen2.5-7B-Instruct | sharpsat-td | SimpleGrid | 100% | 63 | 0.744 | 0.317 | +0.427 [+0.331, +0.515] | 0.618 | 0.422 | +0.195 [+0.117, +0.276] |
| hf:Qwen/Qwen2.5-7B-Instruct | sharpsat-td | TwoPackage | 25% | 16 | 0.240 | 0.375 | -0.135 [-0.302, -0.021] | 0.258 | 0.484 | -0.226 [-0.286, -0.168] |
| hf:Qwen/Qwen2.5-7B-Instruct | sharpsat-td | TwoPackage | 100% | 16 | 0.781 | 1.000 | -0.219 [-0.281, -0.125] | 0.689 | 0.998 | -0.308 [-0.357, -0.251] |
| hf:Qwen/Qwen2.5-7B-Instruct | sharpsat-td | TwoPackageOneway | 25% | 20 | 0.279 | 0.400 | -0.121 [-0.200, -0.042] | 0.302 | 0.487 | -0.184 [-0.216, -0.142] |
| hf:Qwen/Qwen2.5-7B-Instruct | sharpsat-td | TwoPackageOneway | 100% | 16 | 0.677 | 1.000 | -0.323 [-0.438, -0.229] | 0.613 | 0.998 | -0.385 [-0.469, -0.308] |
| hf:Qwen/Qwen2.5-7B-Instruct | mc-sat | SimpleGrid | 25% | 41 | 0.351 | 0.366 | -0.015 [-0.142, +0.129] | 0.320 | 0.343 | -0.023 [-0.072, +0.026] |
| hf:Qwen/Qwen2.5-7B-Instruct | mc-sat | SimpleGrid | 100% | 39 | 0.812 | 0.564 | +0.248 [+0.146, +0.358] | 0.678 | 0.621 | +0.057 [-0.003, +0.127] |
| hf:Qwen/Qwen2.5-7B-Instruct | mc-sat | TwoPackage | 25% | 7 | 0.310 | 0.429 | -0.119 [-0.262, +0.083] | 0.296 | 0.446 | -0.150 [-0.344, -0.004] |
| hf:Qwen/Qwen2.5-7B-Instruct | mc-sat | TwoPackage | 100% | 10 | 0.717 | 1.000 | -0.283 [-0.417, -0.200] | 0.639 | 0.992 | -0.353 [-0.437, -0.268] |
| hf:Qwen/Qwen2.5-7B-Instruct | mc-sat | TwoPackageOneway | 25% | 17 | 0.235 | 0.235 | -0.000 [-0.222, +0.167] | 0.258 | 0.296 | -0.038 [-0.151, +0.060] |
| hf:Qwen/Qwen2.5-7B-Instruct | mc-sat | TwoPackageOneway | 100% | 16 | 0.750 | 1.000 | -0.250 [-0.385, -0.136] | 0.645 | 0.996 | -0.351 [-0.453, -0.277] |
| hf:Qwen/Qwen2.5-7B-Instruct | stop-rule | SimpleGrid | 25% | 176 | 0.207 | 0.182 | +0.026 [-0.009, +0.061] | 0.188 | 0.182 | +0.006 [-0.008, +0.020] |
| hf:Qwen/Qwen2.5-7B-Instruct | stop-rule | SimpleGrid | 100% | 176 | 0.596 | 1.000 | -0.404 [-0.461, -0.339] | 0.474 | 1.000 | -0.526 [-0.573, -0.470] |
| hf:Qwen/Qwen2.5-7B-Instruct | stop-rule | TwoPackage | 25% | 80 | 0.275 | 0.250 | +0.025 [-0.026, +0.078] | 0.259 | 0.250 | +0.009 [-0.016, +0.035] |
| hf:Qwen/Qwen2.5-7B-Instruct | stop-rule | TwoPackage | 100% | 80 | 0.772 | 1.000 | -0.228 [-0.303, -0.167] | 0.651 | 1.000 | -0.349 [-0.404, -0.304] |
| hf:Qwen/Qwen2.5-7B-Instruct | stop-rule | TwoPackageOneway | 25% | 80 | 0.313 | 0.250 | +0.063 [+0.011, +0.120] | 0.297 | 0.250 | +0.047 [+0.016, +0.078] |
| hf:Qwen/Qwen2.5-7B-Instruct | stop-rule | TwoPackageOneway | 100% | 80 | 0.740 | 1.000 | -0.260 [-0.307, -0.217] | 0.636 | 1.000 | -0.364 [-0.398, -0.331] |
| hf:Qwen/Qwen2.5-7B-Instruct | stop-rule | ThreePackage | 25% | 40 | 0.126 | 0.125 | +0.001 [-0.054, +0.056] | 0.135 | 0.125 | +0.010 [-0.014, +0.033] |
| hf:Qwen/Qwen2.5-7B-Instruct | stop-rule | ThreePackage | 100% | 40 | 0.282 | 1.000 | -0.718 [-0.775, -0.657] | 0.240 | 1.000 | -0.760 [-0.802, -0.718] |
| hf:Qwen/Qwen2.5-7B-Instruct | stop-rule | FourPackage | 25% | 168 | 0.112 | 0.083 | +0.029 [+0.005, +0.054] | 0.098 | 0.083 | +0.014 [+0.004, +0.026] |
| hf:Qwen/Qwen2.5-7B-Instruct | stop-rule | FourPackage | 100% | 168 | 0.500 | 1.000 | -0.500 [-0.533, -0.466] | 0.397 | 1.000 | -0.603 [-0.625, -0.584] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | max-term | SimpleGrid | 25% | 176 | 0.161 | 0.187 | -0.026 [-0.052, +0.001] | 0.177 | 0.186 | -0.009 [-0.016, -0.001] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | max-term | SimpleGrid | 100% | 176 | 0.243 | 0.545 | -0.302 [-0.339, -0.260] | 0.208 | 0.510 | -0.302 [-0.325, -0.279] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | max-term | TwoPackage | 25% | 80 | 0.253 | 0.444 | -0.191 [-0.253, -0.119] | 0.260 | 0.417 | -0.157 [-0.192, -0.118] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | max-term | TwoPackage | 100% | 80 | 0.328 | 1.000 | -0.672 [-0.743, -0.592] | 0.281 | 0.982 | -0.701 [-0.729, -0.673] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | max-term | TwoPackageOneway | 25% | 80 | 0.312 | 0.447 | -0.135 [-0.202, -0.066] | 0.271 | 0.425 | -0.154 [-0.194, -0.111] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | max-term | TwoPackageOneway | 100% | 80 | 0.343 | 1.000 | -0.657 [-0.710, -0.608] | 0.302 | 0.984 | -0.683 [-0.703, -0.663] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | sharpsat-td | SimpleGrid | 25% | 79 | 0.225 | 0.304 | -0.079 [-0.154, +0.001] | 0.250 | 0.278 | -0.028 [-0.046, -0.009] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | sharpsat-td | SimpleGrid | 100% | 63 | 0.339 | 0.317 | +0.022 [-0.060, +0.118] | 0.302 | 0.422 | -0.120 [-0.186, -0.053] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | sharpsat-td | TwoPackage | 25% | 16 | 0.307 | 0.375 | -0.068 [-0.271, +0.135] | 0.281 | 0.484 | -0.204 [-0.236, -0.171] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | sharpsat-td | TwoPackage | 100% | 16 | 0.250 | 1.000 | -0.750 [-0.812, -0.688] | 0.248 | 0.998 | -0.750 [-0.781, -0.729] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | sharpsat-td | TwoPackageOneway | 25% | 20 | 0.326 | 0.400 | -0.074 [-0.150, +0.001] | 0.273 | 0.487 | -0.213 [-0.240, -0.182] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | sharpsat-td | TwoPackageOneway | 100% | 16 | 0.314 | 1.000 | -0.686 [-0.812, -0.602] | 0.310 | 0.998 | -0.688 [-0.734, -0.649] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | mc-sat | SimpleGrid | 25% | 41 | 0.293 | 0.366 | -0.073 [-0.216, +0.072] | 0.313 | 0.343 | -0.030 [-0.078, +0.017] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | mc-sat | SimpleGrid | 100% | 39 | 0.385 | 0.564 | -0.179 [-0.315, -0.032] | 0.344 | 0.621 | -0.277 [-0.362, -0.183] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | mc-sat | TwoPackage | 25% | 7 | 0.202 | 0.429 | -0.226 [-0.458, +0.083] | 0.254 | 0.446 | -0.192 [-0.261, -0.136] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | mc-sat | TwoPackage | 100% | 10 | 0.189 | 1.000 | -0.811 [-0.833, -0.788] | 0.232 | 0.992 | -0.760 [-0.803, -0.723] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | mc-sat | TwoPackageOneway | 25% | 17 | 0.355 | 0.235 | +0.119 [-0.116, +0.302] | 0.272 | 0.296 | -0.024 [-0.146, +0.093] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | mc-sat | TwoPackageOneway | 100% | 16 | 0.403 | 1.000 | -0.597 [-0.681, -0.536] | 0.338 | 0.996 | -0.658 [-0.691, -0.625] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | stop-rule | SimpleGrid | 25% | 176 | 0.161 | 0.182 | -0.021 [-0.048, +0.006] | 0.177 | 0.182 | -0.005 [-0.012, +0.003] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | stop-rule | SimpleGrid | 100% | 176 | 0.243 | 1.000 | -0.757 [-0.798, -0.707] | 0.208 | 1.000 | -0.792 [-0.819, -0.756] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | stop-rule | TwoPackage | 25% | 80 | 0.253 | 0.250 | +0.003 [-0.049, +0.060] | 0.260 | 0.250 | +0.010 [-0.007, +0.028] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | stop-rule | TwoPackage | 100% | 80 | 0.328 | 1.000 | -0.672 [-0.743, -0.592] | 0.281 | 1.000 | -0.719 [-0.745, -0.693] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | stop-rule | TwoPackageOneway | 25% | 80 | 0.312 | 0.250 | +0.062 [+0.008, +0.115] | 0.271 | 0.250 | +0.021 [+0.005, +0.036] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | stop-rule | TwoPackageOneway | 100% | 80 | 0.343 | 1.000 | -0.657 [-0.710, -0.608] | 0.302 | 1.000 | -0.698 [-0.719, -0.676] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | stop-rule | ThreePackage | 25% | 40 | 0.143 | 0.125 | +0.018 [-0.021, +0.074] | 0.133 | 0.125 | +0.008 [-0.000, +0.016] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | stop-rule | ThreePackage | 100% | 40 | 0.130 | 1.000 | -0.870 [-0.900, -0.844] | 0.118 | 1.000 | -0.882 [-0.896, -0.867] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | stop-rule | FourPackage | 25% | 168 | 0.095 | 0.083 | +0.012 [-0.005, +0.031] | 0.085 | 0.083 | +0.001 [-0.004, +0.007] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | stop-rule | FourPackage | 100% | 168 | 0.110 | 1.000 | -0.890 [-0.914, -0.870] | 0.093 | 1.000 | -0.907 [-0.916, -0.897] |
| jev-latest | max-term | SimpleGrid | 25% | 176 | 0.214 | 0.187 | +0.028 [-0.000, +0.053] | 0.187 | 0.186 | +0.001 [-0.003, +0.006] |
| jev-latest | max-term | SimpleGrid | 100% | 176 | 0.860 | 0.545 | +0.316 [+0.270, +0.361] | 0.557 | 0.510 | +0.047 [+0.030, +0.066] |
| jev-latest | max-term | TwoPackage | 25% | 80 | 0.377 | 0.444 | -0.067 [-0.145, +0.014] | 0.310 | 0.417 | -0.107 [-0.134, -0.081] |
| jev-latest | max-term | TwoPackage | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.914 | 0.982 | -0.068 [-0.083, -0.055] |
| jev-latest | max-term | TwoPackageOneway | 25% | 80 | 0.398 | 0.447 | -0.049 [-0.109, +0.016] | 0.310 | 0.425 | -0.115 [-0.142, -0.087] |
| jev-latest | max-term | TwoPackageOneway | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.920 | 0.984 | -0.064 [-0.078, -0.051] |
| jev-latest | sharpsat-td | SimpleGrid | 25% | 79 | 0.287 | 0.304 | -0.017 [-0.083, +0.051] | 0.258 | 0.278 | -0.020 [-0.033, -0.005] |
| jev-latest | sharpsat-td | SimpleGrid | 100% | 63 | 0.926 | 0.317 | +0.608 [+0.534, +0.676] | 0.658 | 0.422 | +0.235 [+0.198, +0.273] |
| jev-latest | sharpsat-td | TwoPackage | 25% | 16 | 0.344 | 0.375 | -0.031 [-0.292, +0.115] | 0.317 | 0.484 | -0.168 [-0.221, -0.131] |
| jev-latest | sharpsat-td | TwoPackage | 100% | 16 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.896 | 0.998 | -0.101 [-0.126, -0.077] |
| jev-latest | sharpsat-td | TwoPackageOneway | 25% | 20 | 0.400 | 0.400 | -0.000 [-0.100, +0.092] | 0.321 | 0.487 | -0.165 [-0.189, -0.140] |
| jev-latest | sharpsat-td | TwoPackageOneway | 100% | 16 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.902 | 0.998 | -0.096 [-0.129, -0.064] |
| jev-latest | mc-sat | SimpleGrid | 25% | 41 | 0.378 | 0.366 | +0.012 [-0.088, +0.112] | 0.326 | 0.343 | -0.016 [-0.050, +0.011] |
| jev-latest | mc-sat | SimpleGrid | 100% | 39 | 0.949 | 0.564 | +0.385 [+0.272, +0.496] | 0.731 | 0.621 | +0.109 [+0.053, +0.172] |
| jev-latest | mc-sat | TwoPackage | 25% | 7 | 0.143 | 0.429 | -0.286 [-0.500, +0.000] | 0.279 | 0.446 | -0.167 [-0.215, -0.132] |
| jev-latest | mc-sat | TwoPackage | 100% | 10 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.854 | 0.992 | -0.139 [-0.173, -0.098] |
| jev-latest | mc-sat | TwoPackageOneway | 25% | 17 | 0.500 | 0.235 | +0.265 [+0.090, +0.407] | 0.350 | 0.296 | +0.054 [-0.067, +0.175] |
| jev-latest | mc-sat | TwoPackageOneway | 100% | 16 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.859 | 0.996 | -0.138 [-0.189, -0.099] |
| jev-latest | stop-rule | SimpleGrid | 25% | 176 | 0.214 | 0.182 | +0.033 [+0.004, +0.059] | 0.187 | 0.182 | +0.005 [+0.001, +0.009] |
| jev-latest | stop-rule | SimpleGrid | 100% | 176 | 0.860 | 1.000 | -0.140 [-0.192, -0.089] | 0.557 | 1.000 | -0.443 [-0.478, -0.399] |
| jev-latest | stop-rule | TwoPackage | 25% | 80 | 0.377 | 0.250 | +0.127 [+0.040, +0.219] | 0.310 | 0.250 | +0.060 [+0.034, +0.086] |
| jev-latest | stop-rule | TwoPackage | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.914 | 1.000 | -0.086 [-0.098, -0.075] |
| jev-latest | stop-rule | TwoPackageOneway | 25% | 80 | 0.398 | 0.250 | +0.148 [+0.081, +0.221] | 0.310 | 0.250 | +0.060 [+0.038, +0.085] |
| jev-latest | stop-rule | TwoPackageOneway | 100% | 80 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.920 | 1.000 | -0.080 [-0.093, -0.068] |
| jev-latest | stop-rule | ThreePackage | 25% | 40 | 0.179 | 0.125 | +0.054 [+0.012, +0.100] | 0.143 | 0.125 | +0.018 [-0.003, +0.040] |
| jev-latest | stop-rule | ThreePackage | 100% | 40 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.921 | 1.000 | -0.079 [-0.097, -0.061] |
| jev-latest | stop-rule | FourPackage | 25% | 168 | 0.240 | 0.083 | +0.157 [+0.117, +0.197] | 0.162 | 0.083 | +0.079 [+0.065, +0.093] |
| jev-latest | stop-rule | FourPackage | 100% | 168 | 1.000 | 1.000 | +0.000 [+0.000, +0.000] | 0.938 | 1.000 | -0.062 [-0.069, -0.054] |

## Same prompt against plain prompt

Same files. The plain prompt leaves out the clock and the final-slice rule. Differences are plain minus same, with 95% intervals from resampling problems.

| model | evidence | files | plain acc | same acc | acc diff | plain P(true) | same P(true) | P(true) diff |
|---|---|---|---|---|---|---|---|---|
| gpt-5.4-mini | 25% | 80 | 0.243 | 0.232 | +0.012 [-0.043, +0.065] | 0.253 | 0.247 | +0.006 [-0.005, +0.017] |
| gpt-5.4-mini | 100% | 80 | 0.971 | 0.971 | +0.000 [-0.027, +0.029] | 0.800 | 0.844 | -0.044 [-0.072, -0.016] |
| gpt-6-luna | 25% | 80 | 0.253 | 0.281 | -0.028 [-0.066, +0.008] | 0.262 | 0.267 | -0.004 [-0.012, +0.004] |
| gpt-6-luna | 100% | 80 | 0.976 | 0.922 | +0.053 [+0.017, +0.087] | 0.677 | 0.713 | -0.036 [-0.067, -0.008] |
| hf:Qwen/Qwen2.5-7B-Instruct | 25% | 80 | 0.275 | 0.295 | -0.020 [-0.080, +0.040] | 0.247 | 0.260 | -0.013 [-0.037, +0.012] |
| hf:Qwen/Qwen2.5-7B-Instruct | 100% | 80 | 0.727 | 0.725 | +0.002 [-0.083, +0.079] | 0.585 | 0.594 | -0.009 [-0.065, +0.052] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | 25% | 80 | 0.274 | 0.226 | +0.048 [-0.023, +0.120] | 0.249 | 0.249 | -0.000 [-0.020, +0.018] |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | 100% | 80 | 0.305 | 0.327 | -0.022 [-0.109, +0.068] | 0.278 | 0.283 | -0.005 [-0.037, +0.031] |
| jev-latest | 25% | 80 | 0.256 | 0.283 | -0.028 [-0.071, +0.019] | 0.249 | 0.257 | -0.008 [-0.017, -0.000] |
| jev-latest | 100% | 80 | 1.000 | 0.935 | +0.065 [+0.025, +0.104] | 0.876 | 0.645 | +0.231 [+0.190, +0.268] |

## Failed answers

| model | variant | status | finish reason | calls |
|---|---|---|---|---|
| hf:Qwen/Qwen2.5-7B-Instruct | plain | ok | stop | 4 |
| hf:Qwen/Qwen2.5-7B-Instruct | same | ok | stop | 38 |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | plain | ok | stop | 10 |
| hf:meta-llama/Meta-Llama-3-8B-Instruct | same | ok | stop | 144 |

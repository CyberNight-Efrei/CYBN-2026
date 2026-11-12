Le message du ticket est encodé en ROT13, y compris le début du flag : `PLOA` devient `CYBN`. On peut décoder toute la phrase avec Python :

```bash
python -c "import codecs; print(codecs.decode('Fv gh yvf pr gvpxrg, tneqr abger frperg : PLOA{y3_ie41_f3pe3g_p3fg_dh3_y3_fg4ss_q0eg_q3w4}.', 'rot_13'))"
```

La sortie est :

```text
Si tu lis ce ticket, garde notre secret : CYBN{l3_vr41_s3cr3t_c3st_qu3_l3_st4ff_d0rt_d3j4}.
```

Le flag à soumettre est `CYBN{l3_vr41_s3cr3t_c3st_qu3_l3_st4ff_d0rt_d3j4}`. Le décodage manuel ou un outil ROT13 donne le même résultat.

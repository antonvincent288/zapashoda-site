# -*- coding: utf-8 -*-
"""
Запас хода — генератор SEO-сайта v5 (Apple-дизайн).
Разделы: 137 моделей, 12 руководств, каталог новостей (RSS + своя страница у каждой),
VIN-справочник (хаб + бренды), карта зарядных станций (OSM/Overpass), llms.txt,
OG-карточки (PIL), поиск, sitemap, robots, 404.
Самодостаточен: данные моделей зашиты в DATA_B64. Запуск: python3 build.py [папка] (по умолчанию _site).
Домен: переменная окружения SITE_DOMAIN (по умолчанию https://zapashoda-ev.ru).
"""
import gzip, base64, json, os, re, sys, html, shutil
from datetime import date

DATA_B64 = (

"H4sIAKon4moC/+29C3MbR5In/lX6fOENIIxmo/EGcbMbFElTskVJFkVa9sWGo0m2yDZBNAcPStDGKSTRz7NHsj0zN3fzsMczu3cbsf+NpShRovhShO8D/MGvMJ/kKjOruqsKDRCkHqakjpixSBBAd1f9Misfv8z8pzdWHK/WeGPY+Kc3Jk6ZaRt/8ubZP/z3lIFvgRc6Pxzc7Gx1Ng8+7ax3dozOXmfd6Px753edH42/3fwN/L558Hlns7NrdB511g9uHtztPOhsHdw++Prg1sHdYeNgzehswwvs448PbuHPnxrjM0Znv3MPvutJZ599iv3ZmDhlXTISI6NGZ8sYG02m6GLsa+CzewefsdvYYr8al9orbsYaHZ3KGOwrNjuP4Es22W3CTe6zy++xd27Dd7Obi7wteMCriz4+33fspjb5tTu/F3eahLc0/Cq9hX3rI/q0wf74gP3/CXsbuyTdy98++w4/z249gfc8MpqEh8Cfx+B58MHX8Qu6n4fd/Ra+ut/ZYV8K/+7iDVXoG+BJTfbZm+wbbuHdwsqPjZravcD7+K0MGZ2/whexrdk7uAvXTcFOaNf+6d+Cy96DJftpJ1hQdrf4487BXXb77A10p8HLsOO4RPU5tkT/9Y3FZnOlMWxZzuzVodm2VXOvNqwVp96sufXGordiZdKZvJUuWOmcteQsmdedetu5vug0zSWv6XiNJc813aq71Kz7y/6sV/VMz2TvY6/iO+drbddsNJ3anOeZs+1Vp9U0/dm206i1HbdpLtRdt1b1Fhabs+03/vG/pQjGGQ3WGQXW33cesueC5QO0bLK1yGTg+b47uB2JOwT7E1irg7WDz9laBm//aYcDbZ/tBNujzkbnwcFX7L/rsJkkBeX8mz3EAFaVMLt/8An74yN2xa/Y/p8/NWrcKPJLVAzY/oNvDz4V72FQuKvcIuwTexr2Hnb/bLsOvgCs3UapYNsvIb4v1H8gQeo8oIfdPlhj/26znx7rC4IPu88ecxOki6Atbm4f3stegIdgD7vB3rfJvqGzi4+6iXBKsD/sDtG9snezDej8MfzzTzvJCl/W8D64AGlLwfbjjroUd2ApELnayuJzsLtYP/iCPQNb6BMO4awG4awC4d+A5mSPdB9U3YbR+W1nA39/Ajq3j2LchzezpcV9eYSb8hAhDxjHZWTKfIOt6LeoUizUcYMDCNQJYPixgdfaZfcA6mL74PZwl7p8q78aqwQPAICEN+0cfI3beA8htRuJwpuopPbZL2uauqYzYZ1ubI/dEkoH3C0TRtCs7DN3Dz494ajIaajIyajou560XFu0XLCoIGqdjWE6xm/hQu7CT+yjW2x1mXJiJ8g6SbMmZWx/E7jUpLE2+VbgebKNevIr48LZUWt05Bw7e37V2WUizGSS6yp2sS0G3D3YUrhsclB8fceuxQ4rPAy7z2N2TTQobiHkEPBsZzk8buFNk8K9hyjagDsCHJFioAf4AheIdB7qORAd9vW0aA/Zz9+yD+9xnaivmdB9bLUSI6dOpYwpz112a42UMVJd8RgMat4cfu2Dg5tDoOMe8K/lj6PcAwF4G5AsYf+xKhbdeprOIf4lwuogKwPeG+4Uv2suQnAUClGQ9zlKHK5evTo0X/dW3cxQvWVVrUKhUC7l0uV8LlcsFstpu2TBx8Tb3VX22K1qqzHktiz2gdmqv9CwPvZb9ZpTZX916+3moldbMNt+y6y57rzZ9M2lmn/VdGZ9JhPNRdecm2tk4OWF2abpzDsrTSaB5tyiU1+AD86xj7sNFLa5Zt2bM1fdRW+u6jZMr2a6rbq/4oYSlNckKK/o1W9hzcBohEOLDMmNbj3FEM+Wc52blbfgtGGWppE186RJbhHe0O5CbbtNwgEg1TGJ4sfObdBZt/Ct68ER9gj0MXuNn1bHkpHgWnA06hoRBCK8CIoDWiDS3YBB2vmGXe1bwy4V8mkGYItbhWDvcEsTVuwBILkSGt0Brvfh+TZQNm6i7iYRut/ZJ4X96OC/M7nahQfHzyIaN9kiJ/DGHqBA42eSx8VjsP0FbfsLyvb/yC4FBwhZWGQ+yV4ESBAuP7Ps0Sq8h9rua25T3EJVsS+cpOOcoDtklQqxpBvYxRv4gv1/jS0l+FwI0EfGhWprYYqJgWtlRkEaXFTbn8D+sJui5d5FNaGsNIMlHbGw/yom4P3KqQHA3QbgylYtbedd7p7cCu1MfW/mr7s12BXHcs5fb7Tsc7P597PvlK9WS+GWFLUtKSpb8rtg8VEyAEt4m4/w+Ga2NLPG053vDA0qsIOJTKpkZlN5bkknhdfKvmbn4A7u3WNcCDO0Czubg+7Vb9DAgY+Bm9VlkQv7nX0elhBtW1TicGd49sI2300FUoRfdtvIZjrf0NkAKuCsZ41fZK4CmmdfoGq6zc9cdr1PSWBpVWgZQguIvfXOwW30pPf11dk/7l6VtL0qqfECDsz7+N8NxZW0tF0jc0QWrm10pGB/17h1socLLzxR4ZtxGQ2PbTRm8fMVAOZXuJP3CK3a8vZXpMwmBWCz+xifkbf6+z4baGQPPi3A+u7+tBG5mSktFiHUoiTG+Ik9WBY4w7uf/usK2C33uWbcwqALua7c5FpX13ELzTPYhzX0sWiN4G0l0y4wfA20lBqgQVc8wNuC8wJvAp1Z/PA9NObgzbek6+3T+bYOt85u5RHc2kAavFi2y+l0rlRO5wuZYiZtKxYFvB3OfAfNavjIvF9buOLWFqxVv+0sWleY7Wz9w6rnXv0FMxKajb+D//4C/wZWQ/Pvmv6KN/cL287bxb9bcRZcb/4XuVxJvsYJsfmnz3XH6MqKzP2xS+0pUEADBk0NBC/5Zrvce3w0bKB3uMM9RPz0vdAEgl/Ja9hD+5ZL1C4apPBNBL9UxCXtVN7M8EOHLBpxUG52R+DGZ1IGWu77qC1QQ9E5y6B89u0LyhHJvZcNvMVAQsSjocXOhQVVkPQ4ZNEL43kMInZwMiJCN9AnWRcBju2ukAc3ebbQs8Y12UHneZPUAKhsepkJdGj67GmiiYE4CGN8i66xkJ3gDiFUkgjdGHoe+EYUa3YRsADwnXv82LHzcHptYSzktthDWgV1U/DwA4W8DfEWkna+Sj/tHC6VvjXLLKtiOVfM5zJ52y7kshk7q8glyuScU2+49VVvzgX5WfKXV5ya13ZIkkgIlhxFRtqOed1b9tumKlCr5rJf969boSBoUT07rQjCn7iShRiIFHNVV5/hbBOXdksEAvYoPgESYYmANIZUtrgRKnYeQPaA7R8exTcprmuww+N3UXjWEauGKbovDYe4FJ14gPb4LXgEi134286DikFnBd7WPpxy4nHvY1jyC36oiog6qm96WQm0J8jxg/NnzRhz3RWnakwVky/F/mshMduONhTpvCX5hadmJw+oLUvyzYRi29QN22F4Ex2IaF2xrQCVJXxBfrqb2tGYiI6hBLFQxbMnhalrOz1CjCgyMPTOn+Or4KGEUkpGa1J0x77kiQ3NjMGrbvJzfEuAURhpX6dCBfoQQ8q3+WukNJ9w44BZz+wi+PEKfYLUyT3ZaXmAZ/79iBBtRYvCREc/NAWcCAV3n9/QOskO3cEjXFqM6TBTvyLJubg3TFyA2XObziKQNTkGr8e5QRej0qS49L4hYqePhUm3YeiOgy5Ds62mt+SsNv3AmGh6zPRYZHbARz4zKGaXvI9kWXDbH63U/dmqu9z+qOk2qs5H1113qf7RbHv+I++jBdettj9a8pt+nX1+2b++WPM/qrvse5ofNZg11GgyE6fpVo8mlCv+3KK73FJk0qy5gSi6zQYT0VX/Ol6QGTArdQ++tc1sG7i4W/PgNbprRSEstykk47Prgw5h3/gxiD8z09j7G+zzfnPVbVruavf1rjiNJoV43FADaOFPW83r/D4EskjLoOHOMyN0dAeaUD5lNeOZx0QwXoa6hMyYe3hib0tBsx1ZBD+EnTLSzFi9nDJOfTBmjDSbvpFNAUgo3rHVdTb8OfqLRXgTtQ2EkfC5pCwmSDn8TdNpj9CSAa32BWoWCMesC1OJKTGeO4p+HP2koPgB2o7bFvvrHgoet++4DmCOQvIE4T4Aihbls9XsyR/w3nF71Z3nJtwuqpdH3N61JDBFRELw2A4s6v7xg1S0f/mDbIwpGO1lbqJBbZAZgNYh26/JVmOJifiikXWHjVzaILMQ7X/Z9d40/vbZdxThg5vaEk+j6MydcIX6PDtqRwVf3CsIgWMkznrGSIsJwtloK4PJPnOI6k3QD3UXfLaGtdpe8MEjWuY6iT2Uy1yrNrMI6BHNmiOsA80vZLBr+ktDc/6yNe815vxVt269OZZ+89QI/jdNP5v4z/ibY/abpYz4M/s5jf89JV5n/x2lt9JL4/Knx+gLTebjFQl4H850OWt2Tosv7qLobfMYFErQ+rCBRsp9kaIkwgW4XI86u6luhBlwupOWE3jdR5l+GO6mRnVA3ZQyZsAF7s75buERGLr0eMbe46EkjJrIsUjl9qTHsPBYvs0JA8GTwkMlpt6dNmwFAIGoahFZO99l1bPrbZCPRP4nD4+AzaxwFfZIgQEYt7lGG9TZBN8Pn5VcSoqwJQKNrgT+5GPGBjHjj5dPBnSJiBAOp5ngO3PJih7qFmF4ugHcWvlBDtZ6W+j+MsiOV7viW0x1Nk202S2mOc2GX1swV6qthrkwazbNctkuZYcWm8tcUX44qeKVflcDevs8ucYPF7ipW2BDUVIZndstyqENG2Y2PzSUA7oDxfbMTPqndeZlMw+eaT4zw/6aZX9NnJschQXYJkRTPLDL1wVP9xYZkHBSMSvxDgZTtfAEHs9rmOLaFNg3ZO9WnJjJQdw0OGOfqMoYA5IY4e5sVbrjC6jlHvB43GMLbV4EY+gJ7JMBDTIC33Cf7/tDK9hiAMr9CuXfHxMKtJOpoq/O32fSsIK7xPy4oz003RjaMHyn9ju7aAvQmlCCakPoa/JXAKRvZfJmNv2mwQlHfJcrlIDf4GEmDDyi0Wu8lU5lDS4468YvGASGhvJvHu5NzlrFbClTzGcz5VKJOZPpQimtZQ1N99qKy84FZkCw4wHzeRhyW/HnF5glsOo1VYt1CbxIZoj61ZrvmvXWkr/qzzeaq77VK66HF/Dc2pwLYb2MZdtWusiM1BWnYS7684654sxDWK7mm27TN5t+dckHk5TJmDBW0GcFS8RpodXKbgGs4Vl3vq3cneuFIpfRRE41Yv/lkHgcHseBTfuEKBd0ckjRWY4ZbkHq0eOtUFIAIV+GtJ3DhOTf6eseoYeJVg3EvCW2zg7GvrcRM3IYS8YmWpDksiHOvgyPrCGjlxz2soROmvUJO5rVdjirByokC5OL0xrFAzGEx88M7mk+CCgbkFCGFCCE/7dTqJUwSgRqlCfvgz8biZn3jTNjFK3S3ogeDb4Rj/r7/AhnMOsRUaCv0g/NAZRngD/MQErqDRLjEBe20+zADyxVYdMKvXNIlsovrhaumCNT0965dz4ul3RT0LXhfU33WtNi0umDjOesdAai98WsXc4X7YwV7llO27NcBBNW37Vgb2j1Oftlz0KFSsnznVS3U6F/WOTCxad2MBAoB/xUQyYwS1LGJUArnorsrSjhu7TDisXyDXvtNp5TGNc5+NqCMDAqgSehv7xO6eztILyIKuFbuqHB0jYZO18uFu18vljIMPWe7jLP1Tx9JpPLZ9LpbDaTLuYL+YK0HXltO/Jdnj7h6CtLRjeYhBTzR+4ZUTUw+3Q34Cqh00JWxzroFJGxe0KaBVBqoa+zhhbuevTCcz/u4JYxMjYyJS/2/+GMXk7kALP585B7F5hL3fSfDdnE2qTtf0hcLJJWARRUng+F1RGtAgfZG1zsUyOXVCuQv6CyDTf5+fGAUiTauYQOAzETiDCG0nCP/YOcD/pVZVEkRk+PzLuT5418OqDect4imCw76M0ETyg2TTXaz7rOFWZ12umhIRusTlAo7OsweLfdzS075zUaTg0/Je8fLbhkEO1G3ELAeeab/K14tsiMGxqlIgprS1kwHkCkXPKdKK4MqEDmhlbwNo2plbZxoe4HhCBUL5zXAS9MnT9d0V0eyvjdpvs2Qlo5sy8/DWyAIOK6ZWTTZj4dabLVcMGEHcY86Tm3OuSsrIT2WI29R7yt6l0x3eUldhyasw7z6F1PcjUQVBkdZarl82tIZHAVhIlwYqzwmD4sDDNMwTH4NPCbuCbdw5MEzFbK/OxjpuUO+Yo6dO8cZuP8mTMoPid+FlhVKJVss9jqG5m0yTYo1X0bubRZgJ0TRhnZ1hyMRp7h9M2/ffYd3mfGzCq5Ub656+g03gvicVvsFAePPXlEuoakdJ/1Hmb1PVRsG+bpmZpiEP6j2I59AFwurTuJnJoDFsou+ZdbaBVsiVg7hSOY4oDI6qmqM+/Ksg0vcmYlRlJgP9TEcZF4kEKH7JOLtI9E4HVkQnKvm3u8+G3sbjP5N4d5ski3b1IGj6Cuyxlo+vbgLYJunpLdLF2DV6SDgT8vYIoZuQZXbFy9rB/XtQp3MKfvoGLp2BngUhHfT+M4JuzMjMFg0XTrbWO+zj6QHFaMfCmpIxxiZs53vk8FZB/K8VDhyWbKEKkkIzgYdjkljcxGkbKmdC5ogX3O7aEkWph8WYecNq/EkKJglNjWhR0xxINhKWNyImW86zns9YJ1xq95vzTOjI5Op4zTfm3hl17KGF/1q62my/l+HIW0QoqR9Uf0/L/mqT/wZ25yGeeJInC77x58Ro+NuahdZr7gQ9yioMrn3HTgmTXUhhKVU6wWPu/fo93MyZV8wSrBQiPdAiOKu9qqC9snsPkFwfAWhFsC4pmyInl6+IApyi4Pa0RmfRDQIBtzC+5bXTT5c2IFNdYxrecham5yZcS0L159f6J62W6Y07Kau1YzmVZ2HGdhqTF3teA4SyVnCF5csR0PKcdEDTKBGhSdrNItpmIuzazSTDads/Ml9j/mPPS1ZsuZXCaTLRdyTN7S2Vwxr7w9fIwP5z+cWj1/oXDp8ujsqP/uoiSaeV0081GOozDVJS07jDsuKkJAVtFlG8oxmMDustPI+NvtPW5V5NJkcTEo3WD3aqDBdmsoKbiCnHoIbw3ZAhD736OMwD0L3LctOS+8HpofksQpppZyyJLpFv0FvPJt5NLZFB2Ke6bIpafgmOf3y8Nfe5TRBao8M+HMgNm+fvBpJapEhJlMMvVOmFkVg4tIqMs3hfO8i8kSHkvEL+jHwU9E2Bx32T6wI+8XBmWsO/eTA4Vzl73GXHA0sxs1y5lSsUBHshzTYt7tkF+rejW3DhEP5KjZaXB0a+68X/cXfHPFX3ZrbafKz/V2S8kRO/WGEAo8QupObd5yVp1mHYJitm1CfIyAOqW5C1Nd3sKPuDYboMsMzvBk+8BdA8RqQHn/hL3pM7SvRIED+jf8tOX7sREG0TnDej3UK9IXM6sqJ+lZCE3xU5vHl+9x4tQDUSryOX5MnBv34BxjG8nPDzBY9ILR33eRNMDC6XURJWmACNkSzBsZmAohHg8PngA8+FaQ9DEAzdeU2/LwL9zzlxzvG+i2kgnNnw/tifs8PCyo/sGCsRN3F4OEmhsa+KBqEDisH0vIBHMwbCjQwbkhW4IJty/eFvCVw2fgNyizXj7D2rPExMWRt88g7+/g9lDnyVDyGcSS++jepxCCjCYEqjPzZ3RFtnANtkOneauLbQicI15/cSfggMkoY9to4Ul5H72D4MVUxFdJdAXOASdJY/bHnzv/nDLQIoAgxy0pZCtzOzHScIuj+3F/6Kte04/K7tL3qM8P7kwWnCehwNmJxMAy6tQvVJ22NVJjus+bp2Qxu9EH4v4eBAhVspsVQ4RJ2UXYU7zV+Q/OnNuGx/uTtDaodAPTBnwF0B/BhUdC+1S53HY0p+eI6IO3Qyx69fpCte3MIxDZr5irswpFm7mNoLDNdNlMl8wFvw4MYX/Wb7cgjeCw/1w3m+5s2zHhE8zubq8qaXHQ7kt1v9GAXLdjLqLZarqLjbIVgjWrgVXjQ+AmbWCEMEgFDPfgpCkOHbv5XJGHXrIErweYEyAVDjzxtc6uKcs5Q0eCbGtj3Dw9VR427Gxgo3z2nZHjv1C5BvOy19APIiuCCjRVgz7yNhVoElktKLOTy1T/woD7fUX2MUXN3Cbn3ImwlGbmyphhqjT0ebYiDjaycZ8EJsYGxcD4MgDQ4OaTkQaLaBCAmeE7QMsRxo6FkoVcH07Svh8S1rridd2c7CBABxnoSEX78dwSGhe8bM9SEm7edSS9M2AyvHpNIEKs+EutFSDDQ54OROR604vWxM7SR6cvL4+aM9N+OnNh6f0QqjkNqmog/q/ChyaeJvOxmPAUhomee58SKAETnAxig2mczs4Qs3CDSv7w5N8i+h+kH4BvuRcWs37KSRG3U6KYmSLOgiQhVeGT2QpEn31K01lMF3HViqXoauAyIssiH/vg8gFnFWvx+mMZiNxwm4Fv+NNOcIYQ9LZ56S0BaLPSVY8IF1dq8zHqwfQYX7MkGQhfYOJuB78hAqNKleETKjiSEovRZR/utRW/3jSXIbPWQMpOF8g8RBnTiQqMngksA8DlNcCpThfU/jxCAgzPx27z5MJ6sLtMkAKw4EErmCPly9w4ZJvAid5JbpTuUiSXNCfvk4CZ+M8xsZsvpc1iXj4pu9IQ7MsTUBsGbpsc9pJVl7Sx/RnpM2fOcToC4u+OciIK7wZrglQjTpAP6LSX+AGc3UFc/HUKMktPU0HzbntIspd54LyHY8B9MR5y/1T4iha7+k3SkIcED+ZWrkxcNmeXsrnm+UsrE7T9F06Pa5wt8YoEAVhk6+L4+MxwVDIeb/BRwKqU282EQTw7b9qFN0n93MfHVfjLG2E8JuDWEX8jBY1aFL7yr0RHBXzuzwPrfz/oRbKOnsw+fuNtIyFI/umirHfCV1MGZ+iljJEzl86nDIJX6bJVvnx4baqdhQwucVEsLDmg8j5yH0LWIQY2N6hhEC8z5S0n9tHWWze4fnxEqWC0Y29LsdlbUpSUQovKUoQUdHb0YUoEKSuboqVLJm1mexNTvGuzTVRAzAmw5nFpzEa6aBIhUYqBEzwyXYBRjH/BeOwOiAJmfuh8H83H2FHKIXlkD5Ai1X1GJNJKnW/kjRUXT5wth70GtC4dPQO27P7yQ+mhHO9LJGUm/9L5weqmXwTpVLyZeyF5De7xrkIYoiRNofMN1Giyq9hvAcQl34PYtPd42eKeKD3HlNl6UDyOhRjRbTq6U57pdDlTKJUL5WIuk4WgiLyJ2a5NzOpSr0Xl1w25E1OXNtBbAoTm1X4qUuwfdh4Si0dGPkrFr3gd0D5a0EHi7/NIbicX5YmsXQpkWc1niTwyMxd+DK0Mwf/6aceKurvA6WJ3iBlJPF9wjwmdFGX7NqwI/4osMto3ntQKGrcwOGyDZ8CLmcXf7/NP9EltDCKcknHQqs86NXPZnfecwEC4vshgsWyVcmY6nTaXloE/LMWD/ZV201yFnFK12XBMovq0oSZhllkQwOsCT6tZay8tmqvtVX/eX+VQumSrxwf9LsEIyv9taFhmM8vqx86/dr6xQjMxKXnhD6SY/B2xpkgC2Rf9JLh7s6tV5sJq9+uFNgzddkT3HbwfI3GjxA9jZj2MjYqKf7rNTJCSl/WK/CDTU9a7F613Lmi02B4Nf+iSWmeat5RrdnXYqChRaPTWiS9gqmVBFeO0v+xCGwTrgn/VrUMM1OzuC7OLFiznSaoV54nJCePDKTT+hRsWaatWq95QbcV3q8sBqpreStusO9fdZX81qO9d5PW9bYXNeFxLF/C/vGDWwbcf8uvsmot115lvWOzF6w0TyPNu3fNbUjcUr9FoueYVv1WbHyoVyvlcyYISZzMbIjajITajxW8ZSk2pScnWsIG7JHSfcEHonGZa3U53vgvaQJB4U8RJITgESt7OGZDFkhmyJSQrcv4zBf0DZ544TjweGTQLASVzbmR0SpRiIe4eiT3eIPRpRWSy3/VNj6sxW48uOD2ldnsANIq/iMoHFWYB4DkpCx2pvBA0OI055uU3ZMUb0DUT1CvxzGgd7eCyr0ks37DTkuD5QtiVi4h2gSDehoxBagn4FRFfUPNu8dK5B0FwnXnUdrJi8ADCVpjgFilZJaEXVqsASEiiM5xYQ9Htbe4cKW0BRPURRpRnRiZqbtObSxnYREwUi7M9OYT68IHpeGOnsvNXFvLmxPjcFVl2VpfgPVedatW0i6USswFs+6NsuagIJtWnDUHw12qu+I0mOyRK841C7drHNvcXnVWvWvOlylTF3QS+aChZWU2yyKSodzaveNfYa7VWtSqL2jeKThQsSfS4hvX+C4V055vALdPbEUGjCYO3cyMGvGjFwc8aJpgWyS+qaJ5V6dESEyIexNvcItIEd3LWREcNBfeH1DpzK4b6fUkNK/ReRImgADrwGzeTFUNOAmEHQFGV1NWmMfC21EtGXOuImKLdndJO+in9pEeZ6yrW6TIT/0uOaExmJhMQX6L4Y3r9MrFjNSK1fEBzmcc4abJ3eZmU/OxKINwBk2OqteLWqfKyTrWQep0KMkLlTpdBlw+4Atu0lbo759fmvabn13pTtytGWGUcQRHv3uKofVt0Zut4orK9Q6p3MV2yM4LZC7uU0XZNOe3khw2PMHF8BclFjP1YaBPz0IR4sc/BJR+hoBDD46q7VhxVsiABS6adyBg9QXzswinQtef8bqUt532ZurrNdvd6SnA7a3yanzm8vQHaj0gkrkirgGeTho8fefqP8vf71LsIG+AEMRtJi9GxXDSDFqqRDReZB8Ote7Gr7JKrDhriDjPE4aeglwAy9s2GvJGrJiREPI+9vemb8+AwLLrPS++fHR95W9UN4hU5JkCEB3KSgjyW1dUaKIxYCIIskYf2iZLMw6uUaKGisG52q2q3bGGPiCAQS6HqYEvXRSsEuUIehfwR/hIGBlQ4WXLpHey5clJIASJpq5kfAs4/L5jaN4M6ZKYsh42232q2Zl3j1PXMsntlbnz89Hu9PEL+VhT7q05zbvEfVn8hf0zalkzXtmS6t4Wapip0Zh6JpEbB23zxgiR9L4qyYJ8G749gB4uYPWbcb8pcNYMdmZ/zZhNbFTW6CCjAD+C9BsxqBITe4QQ1jMb1FRTZQxFz1q8tGGe9K64x6c+7TL53iIlJUYBkF4s4YL2qNyUahIc86N4saFSpN7lFuUckNWSkYdcFPYIO8LWhqdtOspfueCoyzJFYOMTd+mBMo9DTCxLO2CvDkUlxOFV2uSwynWzi6Qp/W4P0QApIrAbRZYNQVKqral0LTa1DlFA5qjSmbMLOyLmBTa2z3e9DFskGnfScffMZGhDIwJ1iMGE+fLU1q3Q0jeTJVgbpYFgR7uUXCAapnZWSeKWe5DpFhiHbzKT1dMnxebKwfxl9QzPdG/oF3hopu7vUmGSfc3bAbiNHmfan8JbCW0tMoZyFi5eSMU81+yrsNwVN5G4o0Tkzr36rkEBkL6zrDGm4pkUXlvdb4hVacISjj4+6XiHzbsrPSxUsiiMobn+91+2DAaveL7VhQj2KpkVGIfdVDEQfs/b/wDD5gxGcUaIzA489E532sWhgsYNNejkZLyuTTQ5r7qwWhOatdBmYP4GhsVRvNxaZpVF1Ztuuuew2mo7pmQvV1hI3NCjheL3GbAX2Re48JR6XfE/vd1Rz6v58jb2+7NSXoBPcvAS8rA68bDfwFKPK1Jtt8+bvTITX9Hrodcxjy21/eXwZY48mZxRAhCChE8PEn9aMbJpqCrdl+rfS1nkd8MyDklHGRCRPSUVrtAcTcf+UbRS3Tdln3o0VRWFbhAo1V7L7xjC7vc3d5CDdK/U9EV610mZsUE/l5CEtpyMt14W0qJCyFGiiJn3w/FiBEck+S+j8B0EpVlKZnDp4GdtkLxk3ij2S30KPwcnR0MgRf5ESpYc2l4+KVHS3h48ef9CT/fs8ujSMa10axjXbIqhKZLYYBGIpwMMe6RNRTjPcDVHodW/Y3cV3RzB41eYbwXwM4cOIQRQ3gLId+np6KSU1TzPevqiYIP+z/9QUqBG+ReHDIBS6QaV7ypgSZukEj/iWUXedKoNYKZ2eUcLbRoJdPaABa21WD76qyFlZG6u/jFwe+Ay8blmtXYqCwHJjqVcxcgmLkYvZtMhOwv5mtP3OdO93+fKwmPHxpeiG8ggRv0dhvyjDmQLCqsnw9zZq82DvOhs6R6WbjJKiKhLixWBdq4j372mKXNzsIUFCiXrSTTJ5EgwsWA/ozLzVFRY+HqxZXfwTmXBSCYgRWveLIN6C15Y6b6G0EAz4GIHwBnsMiTiMagLbmNW2NRspxsMK8VrOQWdtM1vicLa4WLEdNO380BDV0SVF/GZTLUqTyRE3svyTUeLYnzdJY15wKEFFLlCGaUKEu592pIJU3teEKiY1P/iFFpSPa/X949pRF2ojyH0g0XsYJ9jYtlCQ2YNP4Eky2beGo6b2PA4bfhOvZYCZPfeQSUh01E1612Fb8muCBOi60P4A1iy72SBninfZsx+5ffAJpguiNoCXUS24NW92fvXK0sfzq7llrY6Kh84oaWlB60ApRIZ9M3hqHftmmKvtWb+OOdFmw+Osu5nz6pFGv0v7gaV5xtt114WHySFBuseywy4VUoWg2zp3FbHTMAYlOjvqLiYH36CgudA2p9/Kmi28R2mDRkbNPutegeubyFX6LGjYR+FScWavYTAqkkB82OiPw0Y00Uc42lBLHqcLPOxVRtu7TI+9w+OGq1xq/gHeYQLEC7Y0mxwmNvnn1O2QHPxP0BoUgSJQIfQQwo3E0/b3nd9ph9QNu5B9q5SLNhpVPNHF1eKFnbC/IudkrvEF3KNhQ123V4mqGVLKe+QCGDFkKCzi2QirNR8yj3UHT6DHYYnrtnjWCKcjrKgNvRX48OkZwR/aQD29Jug8fYT9yDWTAQyyGgyyXTDgnioQ5PfIVQrKs8QTZNSTgbRZRC38eleIlqqzD9tw3fA4pDhW9XkpuCmPPOlXPPtcFjmnLXIuYpElE6EPKZJZcWVhMjCMTgElxbCZn0XvwDZMe5jA0S1HAyl5D8JglpzgZG//ElhgQd/AsNMNWGqHb0r0zBM1xCmiyBVjfPR8nzijzA/lVaVY1rRGfRx2eud/n3qj8tpG5aM2ioZQEHNXNF9D/Xbb4IOrntAqi3E52DeO3X6CrF9D9CrhzYJAJ2GsRZ1ftdVtiNPi46a/BUowr04N4h1mRIZJEDcUoN9DkXxIy0theypEUXeOt47EJpVS9xaI8a2FDJbgVp/LZhS0zShEbUZktAL2A7sFbfP5SHq9xK5QIXz4C6VHohK3iUjCLBpvQQO3QNsfrCX13ervM/XpN67bAtpUpYtvnxmLJPNG0C26E9WAEByaozb17mXPq4M6rjhXLapQs1wTStS6pnTw+rW5amtWntWRs7OcwDaiMfZHdL7+CJRsBo3ct4zxqQtBd4j7PGDAwCpKZcjNwsRZ9IwVvZQlJZ/RW+zMrRi8K//9oIohmvgmRWF4V6SxUWnT8cYNqDXNRM3lfKQMUsGqEaEGdjFK0d1/YxPp5mq0K2pcTDCttreBWZEFe11Qh8QA26/D7B1WqEG8cE/pKEuZDdAe4eQQ9N9RO0AzC4pcPI6M0jcct7bkmwt1v7UCOFqpu42GOefWmm49bGUz715xl5ptE4t2TWjvdsz63hGN5D+iU/w5xjrbRj5tFtWWBIFJy+PP2K2EilVp5gc/Iym4EGHaVLqsTepds4mS9om8rEqNrsCP2vM/6F9g8KGIXwajMPl4Q+zxtlVRRsGFZKuwU764BfZ3YQVTW9Envbr/bXOeuXZCbEgGRNRuD7hVL2j0xGnNWz2te6tqNWv/4Es2DYUoondr0JwrBbFYE42x0JZLqIYZg1o+WelyifSWoFLZAVw8QtD5eDqYuYso2lCmYslP02/emUZryJpFaYYyzgTk/QU2+QGzqc/Quic3UUPLzlRiSp1vg6FB4lFEZwLeILL34Jqfq+L6CMWupzVP+rTuSWtV0nJnpjWeBJP6HevtlTgFV6oskIaXKptHWJObKfVp+i6zD4x0cgDghOllblOoc+z4IyXUoEfgLdJcSt7rVg4744MkkXiyJugTleDOhRmzIwc/tJWghIEoneAzfUSzF9KRoa/4wuyb05pnfVr3rIN1fm8yHzRTCZsZpAweKN+iNCixdD+h2gaszd8OGIvA9U7ng7r9Hptp4aXURJvUeMFUaKSi1wIPbkpD5Qh5/Eb15Jw09CqZ6sGUCXDOkTKkltRvE+YhYHhIYCtSHCe0PNuEnmebgHimMX4ZFl3jxdD4JrWfBp++uM1bGz1GJ1SaP66UMxjk42KkSe8JmQDOpJHhJTOiSdMG2WP/XS6zw6SecE+2UUlwFzGMCq5xZgdImkIQCR4PA3S5v938NVTWJ9UwmdoKCb8KvUK2BGt6fcYGt3d/xSNbQtfzi28avcOUBuYukYEejheYOXMuCHHjQiPTmZuNG1GKbSss+L/JdQ7P+/DArjgmw8mtPMyzJyhZAQ1JD+uy9QnCyj9jKH1CyxZO6NlC2tYJ1192m/W2MWqNG4nRc8lh9OGw+AsDaQU0Y+lxAn/hAWZ8hbW4EXSh+JxmdT6iYAaGhvY4CyhBnhZGCnhLkZ92umEm7kcJndOIhNCM4E52RRUrxMhOVMeS6KL1n2dzou2AU6vvztWd9HvTH2cK429foC0c0xTPmK54wlrtCOuyT8APTcqCsDXlciu7XKhg5uRGLhiPa/Dt5kNYMd91tGJ1sf7/xc6/GVlqLuuSP6GNqAutnlUcuPRdGDuioJj37I326R+L0DupXqoPhwIaOayzScG5zV7dK45UNz6miemYLqa0SMMGH+f3qaA17eBz7HFqE2xuJG9JLyPhLNroblC9eVmVbqoYN9KwSTyo1JQ8qoRivF/2bmG/FV2nbGlg+AEvt9E1pZQOr87DoHuZ9tj9vM+IlvNyt3mkGdwjg1ktMSdeGyKZJ1fAAiGdl8BBMTuIXSJzI1M2aBukvP9g7adojjJHCtiAyArhNZ0wUKgsDyUqinFE7GcaR3TKFL/QUKJgpFEO/5uXhhWN4n8L0usZ+vDb6kQj9l9b/u4S/TNKv4hRR+zvWeW9/BkW2G4O2UWbakxfmE8+OaHqTPpdkidR1WtNTuQ030kr09+goQOYS9Td2i1BMb0nOOnCeGPH3C73wZn7jKwHaWicNMGrew6dNG+ReurOs92Xj0h274ms0rwl2YOuy58pIsBXdxsec2rrJs+CrEtDaJByJQL5m3rRgtqyGUfnVMjhJLl83zPf9vRB19wsCyoMsXkEj/4nxs580LON3/KCu0oV0VJlc84U5c0Nc9ZvLpqwQqadWTWvVBkUri56VTcoeGboS+fSAn8BOjIaOjJR6BiWJgHoc900M5xelLvcd+UBMMcrRd6xFyhqtse0M8ZFnxkVyRBUUdFag90cs7zTlDj/gmL0Kjrw3ruyA+gw8SbyQaoLdpdARBqq6c4t1rw5pofnnIbLR8H1jhvjlFt53mdQbx9RZc8DlX1PzGdbzA4bm9U2Ohu90WHUgY7G33X+GmUc7BulVIGZAgnu+T/E1+y02mQl6BmQ4BHzDfrSLoZFsl8gRNRAR7Z9xA43tyja90BqorgZjN0Gtn5YGhhUVVqDtN4CDuKs7y8zyRvyqlA7uewsONe9mhtuhlNbqPqgxN0GDjUHa9hc9Jq09O9eVDUw/S4tvdpTOz8sSlKIoY79oxMiQIHbIJO6uQmgzDsgSCtkARIlWbvjgSzFxn7awd4rOwjydTn6qBe9jZsTkxekPeb3nzJOtxn6HM/gD9JLFffuiM08d6GneZJXYZp0byJarvBUAUUEGYu7KGykcD7lzdElYaeZueSDr4V2Edhl3KgOhlkQYW+Hz7y7y28PMmIb2OIRSC1foVLbF9N1HwQjfw4h7Q3QN/u5KH0AYEYDZEYDpCX2kmqSeSOWoMGFTLdRCO8YarlLDi/nFu8FLFGtP4t2CkBMhsa2a30LI5sK4qHx90HDwqSGx0QuGeIxkWG/TLg1OOm12t+efVWMxA2pvUtF69EC9Zlhew9OZuq+8QcCFcLHfrbd/Y7RagUBMD6taiT6Xc77U0/04aiBWPIop97zsaLYL0yUPscytMAf3ybhB3HaVYcC0DARZvUptWpSH3SFGrHONkh0xY1sFBTRDIo9Yz/b8YcevJkoEwDyLJ+gavmC8oM8dNvlUbLP92+9q01D3JBcrSAhobUi6G1BDD7WCwCQ0QChaITxaTzDARQp472c4ZpQfZIyxmtt55cpw7ucHAbyMtOhd9CLDAZjBSFc0ZRGFIpQ8eKWeKh9RNrjIAzJ1ojL0IbMuKmIlBn/ltt8EOknwgbk1BSlLZgYCso3nj0cZwc8AZP/cIZV8BAqPaTSp1osaOgRUoWU2mMj0d25bEOEhb9KPoMdnTl/VhNy/oq8q3z2hGdeuHh+2FAPOuEEradC62INNmSfDwGTatRolmHoEiR44wvs/YkFbnwaiGyAJDhXg6fMVVeTWpMwhYBNO4ODm5duBLm2iNbz4qESmd7C/VelbJM3WSEvjTZEKufhE894Y332bAVFI2mEuRRlYzE5eHDzp52kXvvZz7wJHg214CY1hxNfDWkCahglKEbyVAh0P5BPq7NM+md4+vV5r7lXveurQWMJ5APbtmmnrSqOiGxTOziIPiy3oa7OaTpVrwEt47CpRLux5C+rwz2ZzYK7w04mM2suV2tmtpgu2AUZtJku0GYiQDsstXJTBs12818TfJ4RDhCshJM6ooaX8WgYUXA2MFarsJGZIS23OgyE2lJncKkmM553FWX4xq/whydIiV4XeSeIC8C0AWQ5gxRGwBplVe9b8UilCwSiC01uoLqVu+H7JmIew3Kd+0l5xC7ClOdvhOG2y/NAgCtJLx9z1KjUZKqcLRfLtl3+qFjK5W1577Nde686qb40uD3KT83AkF2empFDmmHLXHoQpYPOvsznhCdUVbUSFZAK8nmkBz4nN3BFj0KaCq/wfDWqqfQ8inpCDbROYaKwM+y6pc497i6mrUQ+mgCF9mjUbDgXFOfJlDY8vdGXoRkaCtmk/zhqZsyFa4wMdmIVg0p8GCRJmHA9jxn3xEk7c0kjIolXZF4ae8mYLA4bM5mzgUrgKeOZzGlrJjOh1OppnVqBRjjljwYVW6jbib8j0qzYBlpWFj3D72LZVY4j3GC/Q+zPvGHcrugKzVPXpyanIsKcp2dMpKhu8uHHYuxYOHgrq7cU+L7zP7pKCWTSWyltakOGorYUWox/POfU8bzxmr652HKuuh79vFw0MxaflCYsl8ua3XJZt1quVZ1a07tmjF+yxqeGeTNAnmzdGoReINMJdK5BIgjQ4hgntA0QA0olWdh4VK6OJfqBhW392K+QpE2GwrAlWoJhckbPQaG1sYMFqdtkeBBxNqr3nLoCh5CfFe4EHG4zZ86J7H0EeSDKaY24V6tb8chGu2hsHzTLF60uqdnclonG4ZOfK+dMIdHTWjqZvyCfN+Zpt+4bZbsosaTl7r5B2btMMD4aPzoYr6ukU1JSY0KhKBRRlE+R4C5VX0YxBMl37644oOmO4Rwq8mWpXCGMo3IWyW1hRdH9R84veqx+nz69iM/kEaVfweST6KKgwdjMq/711Trb92VzkS2EyRYCdAns8VW/Ps92vQlf+o/s92V/3q024Ld/egN22GavIWc2qCN9Q7wLXoE6VwurXd++CH9ou04dPv0G2MKc9wOvN5ngY8sFSjZABwm3qQ4DQi4J/NGZQ3IHEDhGUN/Phy/QAeDP4ithLSa1J01nhrAUkN1RMfxLSAaj71rBj6bZzcG5dMPOs5+ywRlP35RJp9+SGxdzyJD60rrhDev9iEUgDG84MfXutGFDF8Nlr7XM7gx+L9Fc6Uc8CvA4GZCF5IQefc/NX4ffk2WfL7P/2/nkkEGN+aRWTcP9G1XQVxTYJ2EQhWo4bQ13U5tA1eHNp41ENqB2JPkj5I2EWOOUwQvmefMiuMJfscZ+K0zfs+eR1gNij0iQXOcFCJJ6pXcUk0Ow8Ffq7i9pJCZ/Sr5i8Lea30RMdf6Dz+n9GpzHDX4rexZwfjkT819ABK0LkzSQYIjhyhTPKzImeJztQMPSsVG4N2qAsFWR2ouT54/Fu8RJk3fLBgjxm89L8Qm1mxiT0DlwApmCxn6BqIgtJj9WJlsqlTLFIv2QzWasxoo7513x2Ps9v9aw3mDiSjKZOUwmiyiTxYlLukjmnoVIGgnb4LXO68ku+cSeGJKQFiViGxc+6t4UtPIwErlUfjSWs5MuZ9TspKsjDLG/Igvqn6I6no5F0v+aIC3UXbdW9RYWm8gDUagdZNgw7Eviku0vLsXLbKnh/5NnLuvykn0uRxjb0su4NrCiSUlWMENCHilatZLM6H/C77iRLaTjY+plOab+yFsdfxGYusL4T0W2aaCsNY9HGRenK3yczmXhK1Dk1cwoHFtIQ6i89TfY20NpyB12eJTx8CgbE/imFyIQfUSAHTbCyvuHZF95uJFJx8JwooThRx7O2RPFhZIo4GXYSv5KzKm5hZ4O9F4UPhL2CN3jnW0fp6KfVvQQCgkZvYCf7w/8EhwB5a4TIB8BeJjn8/wQ3wfkMaxPAqz/HMxoVkH9pyCpKwdAMNqxgawukYqRwlxGQjglhhhO+oRnfYNpVsleiC7IiJamNQWYPn9uXMdzmvCceX54Dl3vLjfhMFBrQywU9ArY0p4kK9HsGiXlgRFDSHrAF7DvyWTSne/4F5ToG7pxFuKLvzPNQASlLfrQLlRbiGMewnkiCpqIAMFTkAl11pUIlPNs2RY1britsT2JJnsIbisqbo+qg6kXwIYgyCt2i0EjyzbC/mub4VwA1Rqf9f2loaqHffZbjQZNyrri/DJgZFvUSV8yyIuH4fZsgYn2WfBiz5bgP2Vq9ETQJef6sEDT0THd3609AsDRvS2H7TCf8Baios/0Woz454n4Pib4yNP6qX/q/FbzU4cM0vs9SLsMwBaHbyEZ+HxGnpfK5TJhEKTLohWbNXAwqepd85zaglUtW5lstlAqZuiHcjpT6h1NKh0mjZPugvNcAkmHxo76mEZS31bYqER+NBW607GNdHJN/3/mJeVYWWeKdBd5AinZ4WUHFP2IWZVnc/KUD8O6ByePVxrEC3ihcI89gZfTE2AgUeaoRljxdloGZdCtK4Aktpocn7monqvPyQjqZ/cUUgV2jSjrB7vZ4pGQZ2sYpuV4cRJvUaqbSCW5l3cM5pMcuvzXiIInmpUJ3BZc082QmaqSvYgdAtVhZIZGVkCwB/oB+1vtiH6GB59SazgwRHeJkRd8SYGalW5hXytkD0QcD326z4ayZw8ke6IVsGApRAVrN42L072EMtv33Lg4HXasGZJEkmQhlEhAWnT2O8slkROjBz0ziIeDxq/aR0emxACjmG2gGfTqWpemYSDh+eCr4d496uRpc+EcD3143Aaa0esRzQDvHnw6HLIybou4uCqD3NvhzU0Q3hmQkd+EHVhFkSxiMKMLRyARODS0S0j5F1OVpv6V/I+cebwnRojcFixSJJmip4TMMB010qRWdhMDHjDf6wAUXEgqeLvL6YxSPxuaoNf5bec79qXfs6f8bed/dX5kx8H/BJdG2e//ZES31efpcrmnSpRVxtyRoabfmsOSGnA2sGAHfw6rtOehNlvqu+mZ83XXWaaJJKvtWSCr4Hvm/WVHktdMf3kdgy9h+hP/hZGCMI09OUgSA974TI/KiGMyZegimex5Jnb7g7Fnc8I9m1+H1hkziMzoeEBCQJO5ImFQIFJVv0i5yvaXqwsO86/8Glty8dPUCxKqHnIQIWf9ZCt2n17iIIFUw45vX1fMPdWXyvXH8ajfqjsL7otx72PP/tX17B8bwaA8TECnRKZknZoLyBwOnvzridl8f8xecrzGolOLMRtj9niY/Y5yysQtx4GuSmTVmnQ+9us90akkmbEttIJOG/jfdkbvuYo+yX6USzxQ5uBpXWLdrM7kesaaYif4pDvB/QJTf+58w7zYf4FKLPagv2XrB/5s50djpkDzpmEdoSTvN3KF9JbCvvtph4YHQSkrLCI9P7Wuwtm7hnf51CWGZWnSH59EAdip9FL9m0FrkC0+HR0+wq/wYx/veubMuQgHoKtJIG9NbystAkPBLfYX3HQRdyTyzBpIaCG4bMUnTnzibEdQS45pCim5aKjvVBPReWBpFwfxPH9WcBqJG0Uwz+yYkPqyOJy/D9LOaA3B2AwxpoozPe4ap7EsF9vemWppXk88l/vjuRzr2Ri3zy5Q0guGGSXDTMWwChDLdhGyXBakmQdk/FvPizSKyUU1cRxH8l5WQ+AP0Oj54JbJZ18+4M3OqF2sGD25L/rZor/EbHVOkua9yeTBLBquleztZc/xlz0F11PTwCGF/05Xm/UXRWJLTDrXIsu7pIxtl8kQlcCVKlqgRQ9vyPSAxkdD26cN7Ky4SUxNdtVYGE46keL76DKvoImVgdnZP3T+v84/V5TGKxEO4XVnxWs6HtJA/Sq0e/D8miU6Grq8o6FnXkPBMButoiQ6mUNE54Pp4gskwaHMJGMT5VU0UY7rDGaUnOTbI+8r+DzlNpqtmmucG7n0s9coxuB8iTXyX4ANY+a7amhFayuwE5hV+g1v7kITN9lt38DGUztQvnh7Lyn1rtunyUZBQ1iet7wvJihFaHLvOihxu5jLlAoZ7FkJ0+TsnFVzrq86tbbZcJaZQl/xV1pVz6mDcld737aon6Dn1CT5UXKho4tObYGySIEMvee1W07NGElDXGUkXcD/Fl+gT9o/uR+L2StV/A6B+h+ZsH3X+bfO/wpLIsneD7p98uaw4UkB+Sq5nxR7A3RD3pLYAPBaxRh35n3jQrXVoLr4h9h2mPkfD5SS4KCA5vpVpw1SpzWRNhe82bo335bkKD+gHL2HcvQeytF76YHMp6chyICHcVz5gYNWmcEXjkaSW+Mk+k8ApRoxqFAdSL4so5Tk3Xbuc0fwQdDnPEJsqd051YopghA9ii2UhaGoZuUkWJy2vEfFtqL2/BPsECqPGMbnwiF61DJW6ZUtGs4NbgFprbYhoRhRJjw2Skm+r6h9szR4/fjgLRwG3nPuqm+Mp4sxvyBW78cL8vy7MjVuOxhjwAnEfJ4aVa4KQjJvak69nL+gtpOgd3A4SedJT59ASWqe+mBMgfJppoQxjDnl1xaMsy+8H10fRN+w01B5b+fjmpeXMiHUE5ClfoBEHKJJQjA7KWiM9evLZz6r/RmE+Vwxxia7aSkjo4Zfq7Z7grY8GGjZV3uwFq5TBcp3Oj8Ihp+BSWtgH1ma1g6EKxrNGTQoHxuVrdxsCuI90QUXydjkfa4mbz/ERpQQCcYsNxd4S/87UaQnBa/ZdD+8XmI2LR37+BOAtkfTm64c5rOpT5AHy47PxBGMV9Ie+HNQ/xkqX0PrpxSJXbsfdj+AuAHqWssYaTZ9XHt8cXoFim0oT39ks2H0HOTypzX0AqBBSjhBdHxa73LD34CEWPHnrvw8lwph1+ZhAYpp/c8xlE+yNfFn7NyPwzc2cEzQPo7XkSdEDRsMRIKvmmJgCviuQ73KQ6Oa5fcUi0xfE4RZHMfK6jx74Pf16fIx7l8iFf4XQGbQYm9ddAqXBln0RGu2H1rH/OrKold7CQBbiKMPL4uK/hYzFw/xWQ7JIqpQzR2iWBda1epJypjfyIEFESPzJVGiEi57QjDfD4LvebUwuvACAgpqqKC7PiyOC7zIVJi6vD0RVOiHoLeZmz+36NYWZh3fOMX+D2lX+Lc0CHXhufckiJ3+V0bZfaezljFtCwhKBUNLw3JMERVI3MjlYHwQr68FJpHAYiGql6dbm3Pq9VbDnGNWJDYx5GlceYaFkvgac2vXHSPBBCOpWqJlCoSxfwfVrnEYLJaI4zbuT4nJn9T/dmATtW/O7AOm3a9CIHcaWj9Pl2N2Z4zW4/ESpNcRqaTF7wNSe0KzrKpZd4UCUaEDBWXTF6cjWgDi4x1vekSvbgfHG5fSpyd5NnayXg73/+K0SdM0aTYtn7qrTCqlS6MNDyuS/E/wVDglfocPad8wxsbHL4ycHbR9+Byxw6xGGobQFYrFdLFAP9jpbO/+4bn0ITJzFufRTSE7cipdHlRG4prX2AZ52oKSoxMmc/YhaJ7I2qUTfQTEyH6l/M3HCk2451Q3tZ5vxa0tqA0cQQVfAA08kdURav/8vEil0DXue/qyUiX1ibsGQzSVTEGumd03WBiLjmdM+k2f4a8XmLP9wTwBWzBReEHDOo8wk4S3GmP3kZMa+WKcdyrXFdCNgX2ygd1j3m1P1CqZt3Nu01FAO80eD2Jzl08aLT1WvC8nPmutarUXFJUM3FnXWVkGhavSJtPZE8JYCLm7Slo4HwcrXraMcEVwafpSy3oq0MLhqB1lq8FQhF1HR9Pw31P4ykg3Of3FNC4aoOYn7un/SnVswba2UNQG4GKAYY+AiflcClQWtgToObE1p6TxztdVE2HC9+eNUacJA7izJ4T4G0cXXreStlypH0Yvos6tOnNLAqnFFxNPiEkXr0PSjsErah4KddGm2WAwRUUap9vHIVOSeROuSxVxobp1/WW3WW8bo2BADFgz9GIshwJcPZ6P97L7Yfn0IQh0qs61tjEOcdlxoDtcuvRiehTGmvOVNFZDPCEtdLdH0TCz8S7zt2ziyHCttX3yqTJoeXsg0ON496kmQ/qit2IUe4xqy8VNc+KmOX2a5jwdUjP9kQpSYhmTfu1jp+4bpz3zQg+U5gcmVl6ctkbP6e5Zl7UD8qiMbzxY01y2WIG/kgocEDc+aV4kCQMyzy5p7ifYDXuNfffdoK0g3tM+1zQ0+BNeBtAF3QsTSMncO7g9RNMGe8wVuV6nLrK1pltrWjX3asMql4qFdE4IjbnKOwxCV9nVttM06+6SX5+XeEB5JWt3tl1bMv7OGFUbjadtur3EeMSJI0mUXY4YnBuh93/LlhA2/wksNg9cyJOCunV/qH4Pi0Cr6j4eFvRST8wdb9X9FReK7QF+uIG3BypFyecGQDWY7uV0OjA+BmmfGVvwcexjYD9Syeed9msLv1S7dY+b703mTzJT3khQTCMeifMy5vXkCmTsuIrlPtTueMtUqz6SFVptzghSRg32VLKFQ/F9eqr8wnlr8rwG8GC+7GzKnHrbRkTn4jDdS8Iblkc2mcx/lUbnHAe0xcNAexpCHKen+Gyd01PZiDaAcXwvBvDTWgdKwu6st6p1+L2chUZS8DSFqI5ScUFdjMBj2AQGxssUvdk3rZxXsnHjq3611XQVnHrmOy5klD2T4OqZUyvOnIs/veO36d/zI8ciRkB9hVxRNfhM4eIhfSUPhXAcM3i5BwxTM+stnJ69jWN8ZSCxq/4xGPcBMrhBXa5TxhizCK64tYUkNsDeDCJVm/ybtsAUUUCADQW2KgYXjkAA8KF3cPoBjoiSJ5VAPEOzwIFup0T9/gG/QXwbBKa7x4/BNjzpER2cr3urbgYihL41axVK6XShnC1ls5lyOV8qFW0pCFhQRw36jaVVb06dZ58FiT4eef/ppVhOsh+JlxdL8UssxVo5bcX42yf/I3PIxB/bKJYLuNlDUVFzzCq5YvQ2jOR2qlWLfm1gfa0lDe1p09AeZ7Up0lFBPP26Y+LAnwVfDqYXlCTqO2RgBSLkmu9MQWoQ/s3BuTg+M5U7SWVdsV33SngWBSVBOrXUvupW1WrY8UvIXTmbj9vbx+h71uhTEopT70+qNJK0jUobzpmDm0Mx/mL8PWv8Kam/dx2vrcX38hTYuxwV14ujKjH+nhZ/Stbv/VbVqy1AHJn5lQstR6uJnvRqHsFxxKtH4PEZW4PIpYicx3Ej7rL5s3Pnfq08LYQsEKjwbbfxtrsIEBg7eIANVfaokYm69j1J9gUldSdiHqq38v/fNNLIkRhxfej8mjjnLHsp422/3lxkmE7GE0djnfrsGxX24D4LiFYMJmgCmiAPgpRzbDppQUkITmg++wiMUJoKhn3Ab7HREAP8Wc4Eu3dIz/iUPKT6CXbRYmvwdJhXco9Tbt1tKKjHnm9vDxodsGJiXGwiH8lEVpOK11x3XnXRrlWdWtO7ZoxfgjDVFLtu063XneSLoWEcoXdQDMhXoTdQxUC9eit4LJ63eIQ29edoXW9x2xo24eAL1MxfCb5/10ilPlPxikqq7cyk1FQrbL05BcPIzxZjuMdwfzadlKO6bKqwVDJX3ujIRZUrn40ZcDEMn3mldVHJVJ1tgSXAkLLo1tvW6ZZz1fXUSQkXizEMYxgeSxteoHWl+jUKpxHCempENY/VdKtO0zcSp0bOjEZis5vpHmMzxuZTekpFJZl1vrbKEHjuzHkVeWcL6Rh6MfSOZyT+eLDGFuwent17nQcGQ1eF1zCz9WS/Mf+7YAFhJMg+wDBOPseAW5U9O6cV1ZaWfrOlejrjVbdZB2bh+LLbdk5IZ8uggEgCdTYNs6HigqETj+c/HNyBUOnT9bQsqpVt3oVFlUNwmT30hz1ytbkXPeMbqtkiEGvHiH05EPtHzPFiwAlIwJyS3BOaSrrqou9eVcsxxoo9yVWxURBD8rlAUskmXfLbvtZEffbD3GVAU9/mIT9zR/V8XA/8EiCTHZ9ghsJXV4x3Lljj0/i7KBuJRGdZ7U99TTNBpy8z2849HJ4xMT/G6NExOgBAS2mtIn1e1Z6T5jkgCLrD56h6ZPjcBTvmTcfgfMahppKSAZp5X8HgmbGhwsk+wWMUvkwGZoABXlP72ECEQS1f0BwOGLXIwpV7Ku4c3GX/v3Vwt6c2VVJKpyZVHHuXsyfgpI9y16WZPjF0T3pHfhm8QLoGWIkz30hEVI3Dm4Qd0DNYWlIyTu+4Tb+lDf+B8/9SxhAtFeOWu69P2UA/SumPYcdRvXk0NhqQmyRhe1HofqUNHSa49camkojCDL0KTW9hwTeKVskqG6Pm2GSM0bi0ZSCrU0kQveO4c77apbMYiaT8QEiKats8Mtqjc3NoEdxJKhCL8XTySqXCoThEFiLtVVE3Evq0BBtG9Mye6k1N+Dir2vjo04VIGGafvUKL0fYyaS8lGXPJqS2pZRTMpD/t5cxLL+AgjOyL3eN0jEF0okBU6l8NcfHyizKmYt3zc8Hm6NE6Jatx6oMx9bhyasbYpOmBu+jUFvDnQYJ1MX5eH7VTTveJ915y2nW/ZpyFTU8ZA09PifHzSumfo5WQlJUEwiW3UdXyWPADRhQ/CDhMEcNDDgm7HjY7pGcvQakteJa3BD34SjaH2IPuG5l82F5wJhs3FHylGgoqgX8uirAOQwai1cTFx36DRufbAj1hEe5/h+3M9JT84cdR3QVX/WrzSsutQg02ILjhX5lbdOoLbr0hNQksZwaRkyloUfSzyklv0Yil4hUZsNPPPMj2TweDHmf/5OifPP1zqnX9+vEmsj5TuNpZME7sYozXV1GLI+qCYoQnZt44+BW2QNrmtp7okbHOsx2db2gkBC0vO9nT9hA40EcZq5bP5AtF7ATbaDpNs+ZcX3WqptYrVlbyObUHp6+ResZrbeeXx0s8P3vNzuQllpSXVVKO4/opSZeR1ryn9SlugvNnGe/ljPDnEv/5pJgjdmyOvF6gVVI0k259zp3X2haNvwcz4cffG8H/nsL/juN/p06CVWLTRWPYvlawLfblo4EZ7WEz+Mv4H/sEqFc7HQP11TWfGeTY/TC40YWFFW2n+5jRP2D0Eh7gHmwc3NvTDx0pK3kv6ISriMao76+4dWNq/ASo7huxrfE6hT6U3NoFt7Xg+k3NQs5gZ1z4l/+QZT+8YKT2qvztRyWO4foK2hhsvxV2psf8tP/7b+o4wf/7b+Yo2BnsXxwodclv1d16jNgYsT8PYpVk4fkVt6od/vWGY0JjkEl/aYn9FAM1BurPA1QlW/e25zR1ip97AsK4N0pxBPf1gqWSnhtz5jw1vzC1UvdooMMLRGbUuMZsrC9fOWDSUPZ9JB5tIL1oS6z5hhEwvjZT+O3GOI5xfMLuHFYU6Epwg7i6b/SEt5I+u+jWnFZVVbwf+m6PUFn2WaLbSCgDV8QoYYOdCmFQAEoUEbR7uFSbAmhK0Wcmcwj/SGIehZeJGUiv1mDingNOQvxmKj3AZIa0wd6Ckz9McCbdBafmGq55yZ1bZMB916kt+L4xjr8fr6L/qczsQC4UMzs+Nl4ze0bJ7s341VW1DPDyaC5tXHSJTged8NivljF+OZc+CdZ3nIt+3eBaPAyuZcDn5dFC2rhUMhJRDPrI1F4Eg/4wqCosem6zrBnI9YZN3lIslaMQom/k41Hrr4c5/1dYS7RyD77ArYFF22DXAjiqIwcJbNFCoST0LvhVt9F01A4WGSYUkPI+3tjz8WkGRGkivKFUlBwn053HOGKsvV9BUPdxOw1cmofYW4h9HLvgyC1d9mkGm8DZZoUBzWysuHNSkxd+WfbmZG+BUBKJkxOqAztFg18nJ/JRNP/nHuGOMGOKcRDxtbJi7HQffOaMxGSr6tSSJ6Qre9z77ZVpoEXRw6ipaaRinqJzu23bfTB9eoosGtC6RroYlKQevacHM0UYTM912eIAWvaXAMy96luLhw3bjvXuK8ousm0lozjaWqmrqZtTfr32guNw0UGNuCrktYKl2n3QWWhpvtsZ84Iz5x6Ln4zacnqql7bE32wjMT2V1CMZ9Ab2c/jnYzbRjDH7cmKWvf405kBOjUnUG3OLrt7qYs6pHcv7elGwpvLruJz1VQy9/eVw9j3btSOPMzomJ9+2lfzhFMN6UyuxMq749eZVn8H3P9vHl5ojmc6yzCh/fgauYSw7L+mx8J9tutx2VzdmOUQcclCC+F2/WQy2rTaCbLdq845al3LGr3m/NLDhAf5UMBLvXjx2K/x9lN+7wXdIEmErAmBHOI9Ggh8x8Fh2QE7pbmqTCxM5MOzbGDcnJi/IKRxxJ1JD9lDhDEPTVLpSCvomwd0AVrEPEYxBV5EIL3zHkPxbA3d7m6H+S/bvfXYjOiiG+ddKuB0ZhdAKXoO9SpI/xl4L2iYNgqB+ktQlkdRWCcX9Hn4/Cu+Q1IleaeMtt46n1AgTRYwl7yIVahPDQhTHQNW8KXgcECnaNqAnU3eD8K2DTwcnkXyPJ8m6dEUmgvyKgIAoBTZsvHtRwJ9tozSXBOS9KyAT7n7EoeJeW2FngLmMk+uH5vxla7bqL1hu1V1q1v1lf9areqZ33Vzy664nC1fxMOF61685xnjVnWvWvbkowRqwHvIpBUsNigMXPMqviIXmpAnNsYLgStbyXY1HOz7zM+r3w/R4rMFfTg2uwvGptWq5P4DLkQDOxgCOAfwstOnTwjeT7gffc17dpzy5a8LPxzIHmOWjJiNFZIZhulc6kmIz9IbIsbvdEI8thZcf208XbczY/bA85beqgOWETO/uZeDaz0gxnx6ZdyfP9wduAeI2UeSPzn9g+1iIndztgil98xB7OTKfrsCuR1AgCd1uh1WCGf9eLWWPxK9Nck3gSN3GUMiXYaClQt15EdHYC/dmRJQlwCJsJfEYBwtB/4jBkJskC3oLUWmNo1GhJPwm3Jrb8NTGRRMzBaQzk+NzxXPnjYkSvDIxU0zHpmes3Y6o3Y6e/ctkB2/ebInmtDxzcXT3/MfOv3a+CT5PwDw3Mgpf+45dLNJOhhiFP0kYvRHGv6B/DeoFtmqZTLrzXXKwrrXwfMb0FIITr2jBNRCgeB+htplqrbh13sUXy9ugpSScCKCCDr6CHYeI6bdBr3HcZrnX+HqXeoRLcHxacrwWYq8R2hRvMER5D1169NE5nb9gy/AdiCT9bxQMdv9sCy625tiGgj46Oz566eL5sYtnZsYryko0IpdCGRF+tKbIdkYfMLZa96tuU2NGVJtkDI5Pzzw75B1dJeZ7W3p4AUnpGQncvqSs/L7RNV70jkYruFSXejtMYUXop6fVFkqW6G2/rk4smWw1mjB2YtKZWzTHcbXZnr1tQpnMWW9hsVk7dm3ys9m/6IKd12TvlAzHRW/Vc9ROMRftS6AE7KnjGR69d4h9KynX8LzVHa4e7+i9k5l0+q1XeSexNoMvBnyP1IE+4H/SmpGNowfyexulSiz+bGvOU2V4xKs/6/0/koRmX2PtqkSkJyZHVQ5ra3mZmSLdA6Fe7Pa82gr0DeaEkOcvOhuE9R4pSIDTCJj7YMD3FjElMHvOazQ0TTtS99pOlBk9YHT2OHvZs7FR9rWVt2z6kH066zpXjA/H4ekvoPF5TLdHiqbAVyV7RCXpL9FRya5wjjzs750LycOaVr52EZ3+c5O/YX//pvMfytxk9OBgarKcXe8aKsBMSAM8noNbQ8gcGkoZPecMVIzgUfla9HjkZ0DgytqHgHnKWWoR4/zoh4cO4KPEHW9kB+yr+tpBtKev/q7rmeMzKSJcfXHwregZok4g63cEZTNqj91mozXrNRZV0sX5VrPK3sGMCiyOOZKSi6hXfx5aLpuCg6sYI+joSu7X7D6AOLjVecDuIVBAIsZIISqIWQGSdtm5CiVgvFC20j1QPmhYA92fjHClO1tRRKFq1RuqrfhudRm0FyYEm95K26w7191lf9W87tTbznytvWhCxGDOa8vYzQ6AXc+c9MZnjpdDeRptxgAZg/FYORQCm3S29lZeucHsZ751R7efDwHAcdqDxn2LXr36kz8Fn2Fri4jheS4tbYPNBkAuPsWz+S6zAAN56g1yJZR6yW/7TTXzMvth7nIkxjPPGeNxn6PXvSQwq4SKz7rXWmra+uKHP4vyjYH52gNTCV5POte16XqTl83s8RrDcd/nsKagiN1H3GfbRI4Yt6sVco/Bcf1UdUqxAdm7bQQEYB8AZCPrFRA0//jf/h+mbhkk8xoCAA=="
)

DATA = json.loads(gzip.decompress(base64.b64decode(DATA_B64.encode("ascii"))).decode("utf-8"))
PAINS = DATA["pains"]
MODELS = DATA["models"]

BRAND_PAINS = {
 'Zeekr': ['ZE-01','ZE-02','ZE-03','ZE-04','ZV-01'], 'Voyah': ['VO-01','VO-02','VO-03','VO-04','VO-05','VO-06','ZV-01'],
 'BYD': ['BYD-01','BYD-02','BYD-03','BYD-04','BAT-03'], 'Denza (BYD)': ['BYD-01','BYD-02','BAT-03'],
 'Li Auto': ['PHEV-02','PHEV-01','PHEV-03'], 'Avatr': ['AV-01','AV-02','BAT-01'], 'Hongqi': ['HO-01','HO-02','HO-03','BAT-01'],
 'Geely': ['GE-01','GE-02','BAT-01'], 'Deepal': ['DE-01','DE-02','PHEV-01','PHEV-03','BAT-01'],
 'MG': ['MG-01','MG-02','MG-03','BAT-01'], 'Kia': ['KR-01','KR-02'], 'Hyundai': ['KR-01','KR-02'], 'Genesis': ['KR-02'],
 'VW': ['EU-01','EU-02'], 'Skoda': ['EU-01','EU-02'], 'Audi': ['EU-01','EU-02'], 'Mercedes': ['EU-01','EU-02'], 'BMW': ['EU-02'],
 'Tesla': ['TS-01','TS-02','BAT-01'], 'Nissan': ['LEAF-01','LEAF-02','BAT-01','ST-05'],
 'Evolute': ['EVOL-01','EVOL-02','BAT-01'], 'Moskvich': ['EVOL-03','BAT-01'], 'AITO': ['AITO-01','BAT-01'],
 'Exeed': ['EX-01','BAT-01'], 'M-Hero': ['MHE-01','ST-05'], 'Mitsubishi': ['T1-02','BAT-01'],
 'Ora': ['BAT-01','BAT-03'], 'Xiaomi': ['BAT-01'], 'XPeng': ['BAT-01'], 'Leapmotor': ['BAT-01'], 'Changan': ['BAT-01'],
 'Lynk & Co': ['BAT-01'], 'JAC': ['BAT-01'], 'Neta': ['BAT-01'], 'Livan': ['BAT-01'], 'Skywell': ['BAT-01'],
 'SWM': ['BAT-01'], 'Kaiyi': ['BAT-01'], 'Wuling / Hongguang': ['BAT-01'], 'Dongfeng': ['BAT-01'], 'GAC': ['BAT-01'],
 'Seres': ['BAT-01'], 'IM Motors': ['BAT-01'], 'iCAR': ['BAT-01'], 'Luxeed (Chery/Huawei)': ['BAT-01'],
 'Stelato (BAIC/Huawei)': ['BAT-01'], 'Onvo (NIO)': ['BAT-01'], 'Lotus': ['BAT-01'], 'HiPhi': ['BAT-01'], 'Roewe': ['BAT-01'],
 'FAW': ['BAT-01']}
GROUP_EXTRA = {'GB/T': ['GB-01','GB-02','GB-03','GB-04','GB-05','GB-06','GB-07','GB-08'],
 'Type1/CCS1': ['T1-01','T1-02'], 'JP/CHAdeMO': ['T1-01','LEAF-01','LEAF-02']}
UNIVERSAL = ['UN-01','UN-02','UN-03','UN-04','UN-05','UN-06','ZM-01','ZM-02','ZM-03','ZM-04','ZM-05',
 'BAT-02','BAT-04','BAT-05','ST-01','ST-02','ST-03','ST-04','T1-03']
PHEV_UNIVERSAL = ['PHEV-01','PHEV-03']

def classify(m):
    ac = (m.get('ac') or ''); dc = (m.get('dc') or '')
    if 'GB/T' in ac or 'GB/T' in dc: return 'GB/T'
    if 'Type 1' in ac or 'CCS1' in dc or 'CCS1' in ac: return 'Type1/CCS1'
    if 'CHAdeMO' in dc or 'CHAdeMO' in ac: return 'JP/CHAdeMO'
    return 'EU'

def pains_for(m):
    grp = classify(m); ids = []
    ids += GROUP_EXTRA.get(grp, [])
    bp = BRAND_PAINS.get(m['brand'].strip())
    ids += bp if bp is not None else ['BAT-01']
    ids += UNIVERSAL
    if any(k in (m.get('type') or '') for k in ['EREV','PHEV','REX']): ids += PHEV_UNIVERSAL
    if 'Leaf' not in m['model']: ids = [i for i in ids if i not in ('LEAF-01','LEAF-02')]
    seen = set(); return [i for i in ids if not (i in seen or seen.add(i))]

_TR = str.maketrans({'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',' ':'-','/':'-','.':'-','(':'',')':'',',':'','+':'','–':'-','—':'-'})
def slug(s):
    return re.sub(r'-+','-', re.sub(r'[^a-z0-9\-]','', s.lower().translate(_TR))).strip('-')

# ================= КОНФИГ =================
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "https://zapashoda-ev.ru")
SITE_NAME = "Запас хода"
TG_CHANNEL = "https://t.me/zapashoda_ev"
TG_BOT_APP = "https://t.me/zapashoda_ev_bot/app"

# ================= APPLE-ДИЗАЙН =================
CSS = r""":root{--bg:#f5f5f7;--card:#fff;--ink:#1d1d1f;--muted:#6e6e73;--line:rgba(0,0,0,.07);--lime:#0071e3;--lime-ink:#ffffff;--max:1040px}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.55;-webkit-font-smoothing:antialiased;font-size:16px}
a{color:inherit}
.wrap{max-width:var(--max);margin:0 auto;padding:0 22px}
main{max-width:var(--max);margin:0 auto;padding:6px 22px 20px}
header{position:sticky;top:0;z-index:50;background:rgba(245,245,247,.72);backdrop-filter:saturate(180%) blur(20px);-webkit-backdrop-filter:saturate(180%) blur(20px);border-bottom:1px solid var(--line)}
.hwrap{max-width:var(--max);margin:0 auto;padding:0 22px;height:52px;display:flex;align-items:center;gap:20px}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;font-weight:700;font-size:17px;color:var(--ink);letter-spacing:-.01em}
.brand svg{display:block;flex:none}
nav{margin-left:auto;display:flex;gap:2px;flex-wrap:wrap;justify-content:flex-end}
nav a{color:var(--ink);opacity:.72;text-decoration:none;font-size:13.5px;padding:7px 12px;border-radius:999px;transition:opacity .15s,background .15s}
nav a:hover{opacity:1;background:rgba(0,0,0,.06)}
nav a.on{opacity:1;background:rgba(0,0,0,.08);font-weight:600}
a:focus-visible,button:focus-visible,.search:focus-visible{outline:2px solid var(--lime);outline-offset:2px;border-radius:10px}
h1{font-size:clamp(30px,5vw,44px);line-height:1.12;letter-spacing:-.03em;font-weight:700;margin:44px 0 14px}
.lede{font-size:clamp(17px,2.3vw,21px);color:var(--muted);line-height:1.45;max-width:760px}
h2{font-size:clamp(22px,3.4vw,30px);letter-spacing:-.018em;font-weight:700;margin:48px 0 14px;scroll-margin-top:70px}
h3{font-size:17.5px;font-weight:600;margin:20px 0 8px;letter-spacing:-.01em}
p{margin:10px 0;max-width:740px;line-height:1.75}
.note{color:var(--muted);font-size:14px;max-width:740px}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px 24px;margin:14px 0;box-shadow:0 1px 2px rgba(0,0,0,.04),0 8px 24px rgba(0,0,0,.05)}
.card h3{margin-top:0}
.sol{background:rgba(0,113,227,.07);border-radius:14px;padding:14px 18px;margin-top:12px;font-size:15px}
.pain-id{display:inline-block;background:#f0f0f3;color:var(--muted);font-size:10.5px;font-weight:700;letter-spacing:.08em;padding:3px 10px;border-radius:999px;margin-bottom:10px}
.tag{border:1px solid var(--line);border-radius:999px;padding:5px 13px;font-size:12.5px;color:var(--muted);font-weight:500;background:#fff;display:inline-block;margin:0 6px 8px 0}
.tag.lime{background:var(--lime);color:var(--lime-ink);border-color:transparent;font-weight:600}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:13px 26px;border-radius:999px;font-weight:600;font-size:15px;text-decoration:none;transition:opacity .2s;cursor:pointer;border:none}
.btn:hover{opacity:.88}
.btn.lime{background:var(--lime);color:var(--lime-ink);box-shadow:0 8px 24px rgba(0,113,227,.18)}
.btn.ghost{background:#e8e8ed;color:var(--ink)}
.btn.ghost:hover{background:#dfdfdF}
.cta{display:flex;gap:12px;flex-wrap:wrap;margin:36px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.grid2{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
.mcard{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 22px;text-decoration:none;color:inherit;display:block;transition:transform .2s,box-shadow .2s;box-shadow:0 1px 2px rgba(0,0,0,.04),0 8px 24px rgba(0,0,0,.05)}
.mcard:hover{transform:translateY(-3px);box-shadow:0 12px 32px rgba(0,0,0,.1)}
.mcard b{font-size:15.5px;letter-spacing:-.01em;display:block}
.mcard span{display:block;font-size:13.5px;color:var(--muted);margin-top:6px}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:16px 0;border:1px solid var(--line);border-radius:14px;background:#fff}
.tw table{min-width:520px;border:none}
table{width:100%;border-collapse:collapse;font-size:14.5px;background:#fff}
td,th{padding:11px 14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:0}
.kicker{font-size:12px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.hero{padding:58px 0 4px;max-width:860px}
.hero h1{margin-top:0}
.hero .ctas{margin-top:26px}
.search{width:100%;max-width:560px;padding:14px 20px;border-radius:999px;border:1px solid var(--line);font-size:16px;background:#fff;margin:24px 0 8px;display:block}
.search:focus{outline:none;border-color:transparent;box-shadow:0 0 0 3px rgba(0,113,227,.25)}
.banner{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 16px;font-size:13.5px;color:var(--muted);margin:14px 0}
.faq{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 20px;margin:10px 0}
.faq summary{cursor:pointer;font-weight:600}
.faq p{margin-top:10px;font-size:14.5px}
.newsdate{font-size:13px;color:var(--muted);font-weight:500}
.newscard{background:#fff;border:1px solid var(--line);border-radius:18px;overflow:hidden;text-decoration:none;color:inherit;display:block;transition:transform .15s,border-color .15s}
.newscard:hover{transform:translateY(-3px);border-color:#d0d0d6}
.newscard img{width:100%;display:block;aspect-ratio:1200/630;object-fit:cover;background:#111}
.newscard .inner{padding:18px 20px 20px}
.newscard b{font-size:16px;letter-spacing:-.01em;display:block;line-height:1.35}
.newscard span{display:block;font-size:13.5px;color:var(--muted);margin-top:8px}
.nmap{height:540px;border-radius:18px;overflow:hidden;border:1px solid var(--line);margin:16px 0;background:#e5e3df}
.leaflet-container{font:inherit;background:#e5e3df}
.src{font-size:12.5px;color:var(--muted);margin-top:10px}
.src a{color:var(--muted);text-decoration:underline;word-break:break-all}
.back{display:inline-block;margin:20px 0 0;color:var(--muted);text-decoration:none;font-size:14px;font-weight:500}
.back:hover{color:var(--ink)}
.cbtns{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 6px}
.cbtn{border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:999px;padding:9px 18px;font-size:14px;font-weight:500;cursor:pointer;transition:background .15s,transform .15s}
.cbtn:hover{background:#f0f0f3;transform:translateY(-1px)}
hr.sep{border:0;border-top:1px solid var(--line);margin:34px 0}
footer{border-top:1px solid var(--line);margin-top:72px;padding:36px 0 64px;color:var(--muted);font-size:13px}
footer .wrap{display:flex;flex-direction:column;gap:10px}
footer a{color:var(--muted)}
@media(max-width:720px){
.hwrap{gap:10px;padding:0 16px;height:48px}
.brand{font-size:15px}
nav a{padding:6px 9px;font-size:12px}
main{padding:4px 16px 16px}
h1{margin-top:28px}
.hero{padding:36px 0 4px}
.grid,.grid2{grid-template-columns:1fr}
.card{padding:18px}
}"""

LOGO_SVG = '<svg width="26" height="26" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="16" fill="#1d1d1f"/><path d="M37 8 L16 38 h14 l-5 18 25-34 H34 l8-14 z" fill="#ffffff"/></svg>'

NAV = [("/index.html","Модели"),("/news/","Новости"),("/pains.html","Проблемы"),("/charging/","Карта ЗУ"),("/vin/","VIN"),("/about.html","О проекте")]

def header_html(active):
    links = "".join('<a href="'+u+'"'+(' class="on"' if u==active else '')+'>'+t+'</a>' for u,t in NAV)
    return '<header><div class="hwrap"><a class="brand" href="/index.html" title="Запас хода">'+LOGO_SVG+'<span>Запас хода</span></a><nav>'+links+'</nav></div></header>'

FOOTER = ('<footer><div class="wrap"><div>Запас хода — практика владения электромобилем в России: разъёмы, зима, зарядка, расходы. '
 '137 моделей, ввезённых в РФ в 2019–2026. Информация из открытых источников; решения носят рекомендательный характер. '
 'При поломке высоковольтной системы обращайтесь в специализированный сервис.</div>'
 '<div>Карта зарядных станций: данные © участники <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> (ODbL), запросы через Overpass API.</div>'
 '<div><a href="https://t.me/zapashoda_ev">Telegram-канал</a> · <a href="https://t.me/zapashoda_ev_bot/app">Мини-приложение</a> · <a href="/feed.xml">RSS</a> · <a href="/llms.txt">llms.txt</a></div></div></footer>')

SHARE_JS = '''<script>
function sharePg(){var t=document.title,u=location.href;
 if(navigator.share){navigator.share({title:t,url:u}).catch(function(){});}
 else if(navigator.clipboard){navigator.clipboard.writeText(t+' — '+u).then(function(){alert('Ссылка скопирована');});}
 else{prompt('Скопируйте ссылку:',u);}
}
document.addEventListener('click',function(e){var a=e.target.closest('a.btn.share');if(a){e.preventDefault();sharePg();}});
</script>'''

def write_page(path, title, desc, body, canonical_rel, og="/assets/og/default.png"):
    d = os.path.dirname(path)
    if d: os.makedirs(d, exist_ok=True)
    doc = ('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
     '<title>' + html.escape(title) + '</title>'
     '<meta name="description" content="' + html.escape(desc) + '">'
     '<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20viewBox=%270%200%2064%2064%27%3E%3Crect%20width=%2764%27%20height=%2764%27%20rx=%2714%27%20fill=%27%231d1d1f%27/%3E%3Cpath%20d=%27M37%208%20L16%2038%20h14%20l-5%2018%2025-34%20H34%20l8-14%20z%27%20fill=%27%23ffffff%27/%3E%3C/svg%3E">'
     '<meta property="og:type" content="article"><meta property="og:image" content="' + SITE_DOMAIN + og + '">'
     '<meta property="og:title" content="' + html.escape(title) + '"><meta property="og:description" content="' + html.escape(desc[:200]) + '">'
     '<meta property="og:url" content="' + SITE_DOMAIN + canonical_rel + '"><meta property="og:site_name" content="' + SITE_NAME + '">'
     '<link rel="canonical" href="' + SITE_DOMAIN + canonical_rel + '">'
     '<link rel="stylesheet" href="/style.css">'
     '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage","name":"' + html.escape(title) + '","description":"' + html.escape(desc[:250]) + '","inLanguage":"ru"}</script>'
     '</head><body>' + header_html(canonical_rel) + '<main>' + body + '</main>' + FOOTER + SHARE_JS + '</body></html>')
    with open(path,'w',encoding='utf-8') as f: f.write(doc)

def src_html(p):
    links = [s for s in p['src'] if s.startswith('http')]
    if links:
        return 'Источники: ' + ' '.join('<a href="'+s+'">'+html.escape(re.sub(r"^https?://(www\\.)?","",s)[:70])+'</a>' for s in links)
    return 'Решение собрано по отзывам владельцев на профильных форумах и сервисах'

PAIN_ARTICLES = [
 ('ne-zaryazhaetsya','Не заряжается электромобиль: 10 причин и что делать','От кабеля и порта до OBC, заземления и прошивки станции. Пошаговая диагностика.',['UN-03','UN-04','BAT-04']),
 ('podogrev-batarei','Подогрев батареи электромобиля: зачем нужен и как включить','Как холодная батарея режет скорость зарядки и запас хода; предпрогрев от сети и в пути.',['UN-01','ZM-01']),
 ('zaryadka-ot-rozetki','Зарядка электромобиля от розетки 220В: время, проводка, безопасность','Сколько реально даёт розетка, какая проводка нужна, почему вышибает автоматы.',['GB-07','GB-08']),
 ('adapter-gbt','Адаптеры для китайских электромобилей: Type2→GB/T, CCS2→GB/T','Какие переходники нужны, как не купить несовместимый, что с батареей питания адаптера.',['GB-01','GB-02','GB-04','GB-05','GB-06']),
 ('zapas-hoda-zimoy','Запас хода электромобиля зимой: почему падает на 30–45% и как вернуть','Физика мороза, отопители, предпрогрев, шины и стиль вождения.',['ZM-01','ZM-02','BAT-03']),
 ('kabel-ne-otdaet','Кабель зарядки не отдаёт из порта: что делать','Почему замок не разблокирует коннектор и где аварийный тросик.',['UN-04']),
 ('12v-akb','12-вольтовый аккумулятор электромобиля: главная тайная боль','Почему садится, какие машины чаще страдают (BYD, Voyah, MG, Kia EV6, Hongqi) и что делать.',['BAT-04']),
 ('lyuchok','Лючок зарядки не открывается на морозе и тугой механизм','Аварийные тросики, прогрев, смазка механизма.',['UN-05','ZV-01']),
 ('udlinitel','Удлинитель и кабель для зарядки электромобиля','Сечение, автоматы, почему дешёвый удлинитель опасен.',['GB-08','UN-06']),
 ('type1-ccs1','Как заряжать электромобиль из США или Кореи в России','Type 1/CCS1: переходники, замена порта, радикальный кейс с перекодировкой.',['T1-01','T1-02','T1-03']),
 ('tesla','Tesla в России: зарядка, адаптеры, Supercharger','EU vs US версии, адаптеры, прогрев батареи на морозе.',['TS-01','TS-02']),
 ('chademo','CHAdeMO: Leaf и другие японские EV','Сети CHAdeMO, деградация от быстрых зарядок, мониторинг батареи.',['LEAF-01','LEAF-02','BAT-01']),
]

RELATED = {
  'ne-zaryazhaetsya': ['Zeekr','BYD','Geely','Voyah','Evolute','Changan'],
  'podogrev-batarei': ['Zeekr','Voyah','BYD','Li Auto','Ora'],
  'zaryadka-ot-rozetki': ['Li Auto','Geely','Changan','BYD','Deepal'],
  'adapter-gbt': ['Zeekr','Voyah','BYD','Avatr','Changan','Exeed','Geely'],
  'zapas-hoda-zimoy': ['BYD','Zeekr','Changan','Ora','MG'],
  'kabel-ne-otdaet': ['Zeekr','Voyah','BYD','MG'],
  '12v-akb': ['BYD','Voyah','MG','Kia','Hongqi'],
  'lyuchok': ['Voyah','Zeekr'],
  'udlinitel': ['Geely','Changan','Li Auto'],
  'type1-ccs1': ['Kia','Hyundai','Tesla','Mitsubishi','Ford'],
  'tesla': ['Tesla'],
  'chademo': ['Nissan'],
}

# ================= VIN-СПРАВОЧНИК =================
VIN_BRANDS = {
 'Zeekr': ('Китай','Группа Geely; заводы в Нинбо и Циндао. Код производителя начинается на L (Китай).'),
 'Li Auto': ('Китай','Заводы в Чанчжоу; код производителя начинается на L.'),
 'BYD': ('Китай','Заводы в Шэньчжэне, Сиане, Чанша и др.; код начинается на L.'),
 'Denza (BYD)': ('Китай','Совместное предприятие BYD и Mercedes-Benz; код начинается на L.'),
 'Voyah': ('Китай','Группа Dongfeng, завод в Ухане; код начинается на L.'),
 'Avatr': ('Китай','Changan + CATL + Huawei; код начинается на L.'),
 'Hongqi': ('Китай','FAW, заводы в Чанчуне; код начинается на L.'),
 'Geely': ('Китай','Заводы в Нинбо и др.; код начинается на L.'),
 'Deepal': ('Китай','Changan; код начинается на L.'),
 'Exeed': ('Китай','Chery; код начинается на L.'),
 'Changan': ('Китай','Заводы в Чунцине; код начинается на L.'),
 'AITO': ('Китай','Seres + Huawei; код начинается на L.'),
 'M-Hero': ('Китай','Dongfeng (Mengshi); код начинается на L.'),
 'Ora': ('Китай','Great Wall Motor; код начинается на L.'),
 'Xiaomi': ('Китай','Завод в Пекине; код начинается на L.'),
 'XPeng': ('Китай','Заводы в Чжаоцине и Ухане; код начинается на L.'),
 'Leapmotor': ('Китай','Код начинается на L.'),
 'Lynk & Co': ('Китай','Geely-Volvo; код начинается на L.'),
 'JAC': ('Китай','Код начинается на L.'),
 'Neta': ('Китай','Код начинается на L.'),
 'Livan': ('Китай','Geely-Renault JV; код начинается на L.'),
 'Skywell': ('Китай','Код начинается на L.'),
 'SWM': ('Китай','Код начинается на L.'),
 'Kaiyi': ('Китай','Код начинается на L.'),
 'Wuling / Hongguang': ('Китай','SAIC-GM-Wuling; код начинается на L.'),
 'Dongfeng': ('Китай','Код начинается на L.'),
 'GAC': ('Китай','Код начинается на L.'),
 'Seres': ('Китай','Код начинается на L.'),
 'IM Motors': ('Китай','SAIC; код начинается на L.'),
 'iCAR': ('Китай','Chery; код начинается на L.'),
 'Luxeed (Chery/Huawei)': ('Китай','Chery + Huawei; код начинается на L.'),
 'Stelato (BAIC/Huawei)': ('Китай','BAIC + Huawei; код начинается на L.'),
 'Onvo (NIO)': ('Китай','NIO; код начинается на L.'),
 'HiPhi': ('Китай','Код начинается на L.'),
 'Roewe': ('Китай','SAIC; код начинается на L.'),
 'FAW': ('Китай','Код начинается на L.'),
 'MG': ('Китай','Современные MG производит SAIC в Китае; исторические — Великобритания.'),
 'Tesla': ('США / Китай','Версии для Европы и РФ — с завода во Фремонте (США, VIN с 1 или 5) или из Шанхая (Китай, LRW). US-версии — порт NACS, EU/CN — CCS2/GB/T.'),
 'Nissan': ('Япония','Leaf собирается в Японии; часть машин для РФ — сборка в Санкт-Петербурге до 2022 года.'),
 'Mitsubishi': ('Япония','Код начинается на J (Япония).'),
 'Kia': ('Корея / Россия','Заводы Кореи (код K) и калининградский «Автотор» (X). Рынок поставки уточняйте по 11-й позиции VIN.'),
 'Hyundai': ('Корея / Россия','Заводы Кореи (код K), Таганрог и Екатеринбург (X).'),
 'Genesis': ('Корея','Завод в Ульсане; код K.'),
 'VW': ('Германия / Россия','Заводы в Вольфсбурге и др. (код W); для РФ — Калуга (X) до 2022 года.'),
 'Skoda': ('Чехия / Россия','Заводы в Млада-Болеславе (код T); для РФ — Калуга и Нижний Новгород (X) до 2022 года.'),
 'Audi': ('Германия','Заводы в Ингольштадте и Неккарзульме; код W.'),
 'Mercedes': ('Германия','Заводы в Зиндельфингене и др.; код W.'),
 'BMW': ('Германия','Заводы в Мюнхене и Лейпциге (код W); для РФ — «Автотор», Калининград (X).'),
 'Evolute': ('Россия','Собран в Липецке на заводе «Моторинвест»; код X.'),
 'Moskvich': ('Россия','Собран в Москве (бывший завод Renault); код X.'),
 'Lotus': ('Англия / Китай','Классика — Хетел (Англия, S); электрические Eletre/Emeya — Ухань (Китай, L).'),
}

VIN_YEAR = [('A',2010),('B',2011),('C',2012),('D',2013),('E',2014),('F',2015),('G',2016),('H',2017),
            ('J',2018),('K',2019),('L',2020),('M',2021),('N',2022),('P',2023),('R',2024),('S',2025),('T',2026)]

VIN_STRUCT = '<h2>Как устроен VIN: 17 символов</h2><div class="tw"><table><tr><th>Позиции</th><th>Название</th><th>Что кодирует</th></tr>'
VIN_STRUCT += '<tr><td>1–3 (WMI)</td><td>Код завода-изготовителя</td><td>1-й символ — регион: <b>L</b> — Китай, <b>J</b> — Япония, <b>K</b> — Корея, <b>W</b> — Германия, <b>1/4/5</b> — США, <b>X</b> — Россия/СНГ, <b>S</b> — Великобритания, <b>T</b> — Чехия/Швейцария, <b>V</b> — Франция/Испания, <b>Z</b> — Италия, <b>Y</b> — Швеция/Финляндия.</td></tr>'
VIN_STRUCT += '<tr><td>4–9 (VDS)</td><td>Описание модели</td><td>Модель, двигатель, кузов. 9-я позиция — контрольная цифра (обязательна для машин американского рынка).</td></tr>'
VIN_STRUCT += '<tr><td>10</td><td>Модельный год</td><td>Код года — таблица ниже. Цикл повторяется каждые 30 лет.</td></tr>'
VIN_STRUCT += '<tr><td>11</td><td>Завод сборки</td><td>Буква/цифра конкретного завода.</td></tr>'
VIN_STRUCT += '<tr><td>12–17 (VIS)</td><td>Серийный номер</td><td>Порядковый номер машины.</td></tr></table></div>'
VIN_STRUCT += '<h2>Код модельного года (10-я позиция)</h2><div class="tw"><table><tr><th>Код</th><th>Год</th><th>Код</th><th>Год</th><th>Код</th><th>Год</th></tr>'
_vin_rows = ''
for _i in range(0, len(VIN_YEAR), 3):
    _trio = VIN_YEAR[_i:_i+3]
    _cells = ''.join('<td>'+c+'</td><td>'+str(y)+'</td>' for c,y in _trio)
    if len(_trio) < 3: _cells += '<td>—</td><td>—</td>'*(3-len(_trio))
    _vin_rows += '<tr>'+_cells+'</tr>'
VIN_STRUCT += _vin_rows + '</table></div>'
VIN_STRUCT += '<p class="note">Буквы I, O, Q, U, Z и цифра 0 в коде года не используются — чтобы не путать с 0, 1, 2 и V.</p>'
VIN_STRUCT += '<h2>Где искать VIN на электромобиле</h2><div class="card">'
VIN_STRUCT += '<p>У EV табличка с VIN обычно в тех же местах, что и у обычных машин:</p>'
VIN_STRUCT += '<p>• в нижнем углу <b>лобового стекла</b> со стороны водителя (виден снаружи);</p>'
VIN_STRUCT += '<p>• на <b>шильдике в проёме водительской двери</b> (B-стойка);</p>'
VIN_STRUCT += '<p>• в <b>документах</b>: ПТС, СТС, ЭПТС, договор купли-продажи, СБКТС.</p>'
VIN_STRUCT += '<p>У части китайских EV продублирован на наклейке в проёме лючка зарядки — удобно сверять при подключении адаптера.</p></div>'
VIN_STRUCT += '<h2>Проверка VIN перед покупкой (особенно параллельный импорт)</h2><div class="card">'
VIN_STRUCT += '<p><b>1. Сверьте VIN во всех местах.</b> VIN на кузове, на табличке и в документах должен совпадать посимвольно. Перебитый VIN — главная красная флаговая история.</p>'
VIN_STRUCT += '<p><b>2. Бесплатная проверка ГИБДД.</b> На сайте <a href="https://гибдд.рф/check/auto">гибдд.рф</a> по VIN бесплатно: история регистраций, ДТП, розыск, ограничения. Это первый шаг всегда.</p>'
VIN_STRUCT += '<p><b>3. ЭПТС и СБКТС.</b> У машин параллельного импорта (Zeekr, Li Auto, Avatr и др.) должен быть электронный ПТС и свидетельство о безопасности конструкции (СБКТС), оформленные на импортёра. Без СБКТС машину не поставят на учёт. Проверьте, что ЭПТС выпущен легально и на этот VIN.</p>'
VIN_STRUCT += '<p><b>4. Код года по 10-й позиции.</b> Сверьте с годом в ЭПТС: расхождение — повод задуматься о легальности ввоза или «омоложении» машины.</p>'
VIN_STRUCT += '<p><b>5. Расшифровка комплектации.</b> Точную расшифровку опций по VIN даёт дилер марки или официальный сервис по запросу — в интернет-справочниках встречаются ошибки.</p></div>'
VIN_STRUCT += '<p class="note">Справочник информационный: не юридическая консультация и не заменяет проверку по официальным базам.</p>'

def vin_brand_page(brand, outdir):
    country, note = VIN_BRANDS[brand]
    models_b = [m for m in MODELS if m['brand'].strip()==brand]
    top = sorted(models_b, key=lambda x: x['freq']!='Массовый')[:6]
    cards = ''.join('<a class="mcard" href="/models/'+slug(m['brand'])+'-'+slug(m['model'])+'.html"><b>'+html.escape(m['brand']+' '+m['model'])+'</b><span>'+html.escape(m['years']+' · '+m['type']+' · '+m['freq']+' ввоз')+'</span></a>' for m in top)
    parts = []
    parts.append('<a class="back" href="/vin/">← Все бренды VIN-справочника</a>')
    parts.append('<h1>VIN ' + html.escape(brand) + ': где табличка, код года и проверка истории</h1>')
    parts.append('<p class="lede">Код производителя, позиция модельного года и места расположения таблички у ' + html.escape(brand) + ', ввезённых в Россию.</p>')
    parts.append('<div class="card"><h3>Страна сборки и код завода</h3><p><span class="tag lime">' + html.escape(country) + '</span></p><p>' + html.escape(note) + '</p>')
    parts.append('<p class="note">Первый символ VIN соответствует региону производства: L — Китай, J — Япония, K — Корея, W — Германия, X — Россия/СНГ.</p></div>')
    parts.append(VIN_STRUCT)
    if cards:
        parts.append('<h2>Модели ' + html.escape(brand) + ' в нашей базе</h2><div class="grid2">' + cards + '</div>')
    parts.append('<h2>Что проверить по VIN ' + html.escape(brand) + ' перед покупкой</h2><div class="card">')
    parts.append('<p>Машины ' + html.escape(brand) + ' в РФ чаще всего ввезены по параллельному импорту или из Кореи — значит, ключевые проверки: совпадение VIN на кузове и в ЭПТС, наличие СБКТС, история ДТП по базе ГИБДД, код модельного года на 10-й позиции.</p>')
    parts.append('<p>Проверить историю бесплатно: <a href="https://гибдд.рф/check/auto">сервис ГИБДД по VIN</a>. Расшифровку комплектации — у дилера марки.</p></div>')
    parts.append('<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Подобрать комплект зарядки</a><a class="btn ghost" href="' + TG_CHANNEL + '">Канал «Запас хода»</a><a class="btn ghost share" href="#" onclick="sharePg();return false;">Поделиться</a></div>')
    body = ''.join(parts)
    sl = 'vin/'+slug(brand)+'.html'
    write_page(os.path.join(outdir, sl), 'VIN ' + brand + ': где табличка, код года, проверка истории — Запас хода',
        'Расшифровка VIN ' + brand + ' (' + country + '): код завода, модельный год на 10-й позиции, где находится табличка, бесплатная проверка ГИБДД и ЭПТС/СБКТС для параллельного импорта.',
        body, '/' + sl, og='/assets/og/vin-'+slug(brand)+'.png')
    return sl

def model_page(m, outdir):
    grp = classify(m); ids = pains_for(m)
    pname = m['brand'] + ' ' + m['model']
    sl = 'models/' + slug(m['brand']) + '-' + slug(m['model']) + '.html'
    pain_html = ''.join(
        '<div class="card"><span class="pain-id">' + i + '</span><h3>' + html.escape(PAINS[i]["pain"]) + '</h3>'
        '<p class="note">Кому актуально: ' + html.escape(PAINS[i]["who"]) + '</p>'
        '<div class="sol"><b>Решение:</b> ' + html.escape(PAINS[i]["sol"]) + '</div>'
        '<p class="src">' + src_html(PAINS[i]) + '</p></div>' for i in ids)
    rows = ('<tr><td>AC (медленная)</td><td>' + html.escape(str(m.get("ac") or "—")) + '</td></tr>'
     '<tr><td>DC (быстрая)</td><td>' + html.escape(str(m.get("dc") or "—")) + '</td></tr>'
     '<tr><td>Бортовое зарядное (OBC)</td><td>' + html.escape(str(m.get("obc") or "—")) + '</td></tr>'
     '<tr><td>Мощность DC</td><td>' + html.escape(str(m.get("dcp") or "—")) + '</td></tr>'
     '<tr><td>Рынок вывоза</td><td>' + html.escape(str(m.get("market"))) + '</td></tr>')
    sol_block = html.escape(str(m['sol'])) if m.get('sol') else ''
    note = html.escape(str(m['note'])) if m.get('note') else ''
    srcrow = ('<p class="src">Источник спецификации: <a href="' + m["src"] + '">' + re.sub(r"^https?://(www\\.)?","",str(m["src"])) + '</a></p>') if m.get('src') and str(m['src']).startswith('http') else ''
    vin_link = ''
    if m['brand'].strip() in VIN_BRANDS:
        vin_link = ('<div class="card"><h3>VIN и история машины</h3><p>Владеете или выбираете с пробегом? Смотрите страницу '
          '<a href="/vin/'+slug(m['brand'])+'.html">VIN ' + html.escape(m['brand']) + '</a>: где табличка, код модельного года на 10-й позиции, '
          'бесплатная проверка ГИБДД и что проверить в ЭПТС/СБКТС у параллельного импорта.</p></div>')
    faq = ('<details class="faq"><summary>Каким разъёмом заряжается ' + html.escape(pname) + '?</summary>'
     '<p>AC: ' + html.escape(str(m.get("ac") or "—")) + '. DC: ' + html.escape(str(m.get("dc") or "—")) + '. Разъём зависит от рынка вывоза: ' + html.escape(str(m.get("market"))) + '.</p></details>'
     '<details class="faq"><summary>Можно ли зарядить ' + html.escape(pname) + ' от обычной розетки 220В?</summary>'
     '<p>Да, портативным зарядным устройством: обычная розетка даёт примерно 2,3–3,5 кВт. Паспортные «6–8 часов до 100%» относятся к станции 7 кВт — от розетки дольше. Нужны отдельная линия и автомат 32А.</p></details>'
     '<details class="faq"><summary>Какие типичные проблемы у ' + html.escape(pname) + '?</summary><p>Смотрите блок «Боли и решения» выше — собрано по отзывам владельцев и профильных сервисов, со ссылками на первоисточники.</p></details>')
    faq_ld = '<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
          {"@type": "Question", "name": "Каким разъёмом заряжается " + pname + "?", "acceptedAnswer": {"@type": "Answer", "text": "AC: " + str(m.get('ac') or '—') + ". DC: " + str(m.get('dc') or '—') + ". Разъём зависит от рынка вывоза: " + str(m.get('market')) + "."}},
          {"@type": "Question", "name": "Можно ли зарядить " + pname + " от обычной розетки 220В?", "acceptedAnswer": {"@type": "Answer", "text": "Да, портативным зарядным устройством: розетка даёт 2,3–3,5 кВт. Нужны отдельная линия и автомат 32А; от розетки до 100% дольше, чем от станции 7 кВт."}},
          {"@type": "Question", "name": "Какие типичные проблемы у " + pname + "?", "acceptedAnswer": {"@type": "Answer", "text": "Смотрите раздел «Боли и решения»: типичные поломки и жизненные ситуации владельцев этой модели с решениями и ссылками на первоисточники."}}
        ]
    }, ensure_ascii=False) + '</script>'
    parts = []
    parts.append('<h1>' + html.escape(pname) + ': какой разъём зарядки, типичные проблемы и решения</h1>')
    parts.append('<p><span class="tag lime">' + m['years'] + '</span><span class="tag">' + m['type'] + '</span><span class="tag">' + grp + '</span><span class="tag">' + m['freq'] + ' ввоз</span></p>')
    parts.append('<p class="note">Важно: разъём зависит от рынка вывоза, а не от марки — проверяйте по фото лючка или VIN.</p>')
    parts.append('<h2>Разъёмы и мощность зарядки</h2><div class="tw"><table>' + rows + '</table></div>')
    parts.append(vin_link)
    if sol_block:
        parts.append('<div class="card"><h3>Что понадобится для зарядки</h3><p>' + sol_block + '</p></div>')
    if note:
        parts.append('<p class="note"><b>Примечание:</b> ' + note + '</p>')
    parts.append(srcrow)
    parts.append('<h2>Боли и решения для владельцев</h2>')
    parts.append(pain_html)
    parts.append(faq)
    parts.append(faq_ld)
    parts.append('<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Подобрать комплект зарядки</a><a class="btn ghost" href="' + TG_CHANNEL + '">Канал «Запас хода»</a><a class="btn ghost share" href="#" onclick="sharePg();return false;">Поделиться</a></div>')
    body = ''.join(parts)
    write_page(os.path.join(outdir, sl),
        pname + ' — какой разъём зарядки, типичные проблемы и решения | Запас хода',
        'Разъёмы AC/DC ' + pname + ' (' + m["years"] + '), зарядка от розетки и на станциях, реальные проблемы владельцев и проверенные решения. ' + grp + '-стандарт, ' + m["freq"] + ' ввоз в РФ.',
        body, '/' + sl, og='/assets/og/m-'+slug(m['brand'])+'-'+slug(m['model'])+'.png')
    return sl

# ================= НОВОСТИ =================
def load_news(data_dir):
    ndir = os.path.join(data_dir, 'news')
    items = []
    if os.path.isdir(ndir):
        for fn in sorted(os.listdir(ndir)):
            if fn.endswith('.json'):
                try:
                    with open(os.path.join(ndir, fn), encoding='utf-8') as f:
                        it = json.load(f)
                    it['_file'] = fn
                    items.append(it)
                except Exception as e:
                    print('WARN news file:', fn, e)
    items.sort(key=lambda x: x.get('date',''), reverse=True)
    return items

def load_news_map(data_dir):
    p = os.path.join(data_dir, 'news_map.json')
    if os.path.exists(p):
        try:
            with open(p, encoding='utf-8') as f: return json.load(f)
        except Exception: pass
    return {}

def news_slug_page(it):
    return '/news/' + it['date'] + '-' + it['slug'] + '.html'

def month_ru(mn):
    return ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'][mn-1]

def fmt_date(d):
    try:
        y,m,dd = d.split('-'); return dd + ' ' + month_ru(int(m)) + ' ' + y
    except Exception: return d

def news_page(it, outdir, news_map):
    sl_file = it['date'] + '-' + it['slug'] + '.html'
    discuss = TG_CHANNEL
    mid = news_map.get(it['slug'])
    if mid: discuss = TG_CHANNEL + '/' + str(mid)
    parts = []
    parts.append('<a class="back" href="/news/">← Все новости</a>')
    parts.append('<h1>' + html.escape(it['title']) + '</h1>')
    parts.append('<p class="newsdate">' + fmt_date(it['date']) + ' · Запас хода</p>')
    parts.append(it['body'])
    rel_models = it.get('related') or []
    if rel_models:
        parts.append('<h2>Связанные страницы справочника</h2><p class="note">' + ', '.join(rel_models) + '</p>')
    parts.append('<hr class="sep">')
    parts.append('<div class="cta"><a class="btn lime" href="' + discuss + '">Обсудить в Telegram</a>'
     '<a class="btn ghost" href="' + TG_BOT_APP + '">Каталог аксессуаров</a>'
     '<a class="btn ghost share" href="#" onclick="sharePg();return false;">Поделиться</a></div>')
    body = ''.join(parts)
    write_page(os.path.join(outdir,'news',sl_file), it['title'] + ' | Запас хода',
        it.get('teaser') or it['title'], body, news_slug_page(it),
        og='/assets/og/n-'+it['date']+'-'+it['slug']+'.png')

def news_index(items, outdir):
    cards = ''
    for it in items:
        cards += ('<a class="newscard" href="' + news_slug_page(it) + '">'
          '<img src="/assets/og/n-' + it['date'] + '-' + it['slug'] + '.png" alt="" loading="lazy">'
          '<div class="inner"><span class="newsdate">' + fmt_date(it['date']) + '</span>'
          '<b>' + html.escape(it['title']) + '</b><span>' + html.escape(it.get('teaser') or '') + '</span></div></a>')
    body = ('<div class="hero"><div class="kicker">Лента</div><h1>Новости и разборы</h1>'
     '<p class="lede">Практика владения EV в России: цифры, зима, зарядка, новые модели. Коротко и по делу.</p>'
     '<input class="search" id="q" placeholder="Поиск по новостям: зима, адаптер, батарея…"></div>'
     '<div class="grid" id="nlist">' + cards + '</div>'
     '<script>document.getElementById("q").addEventListener("input",function(){var q=this.value.toLowerCase();'
     'document.querySelectorAll("#nlist .newscard").forEach(function(c){var t=(c.textContent||"").toLowerCase();'
     'c.style.display=t.indexOf(q)>=0?"":"none"});});</script>')
    write_page(os.path.join(outdir,'news','index.html'), 'Новости о электромобилях в России | Запас хода',
        'Лента: цифры, зима, зарядка, новые модели EV в России. Каждая новость — отдельная страница с разбором.', body, '/news/')

def news_feed(items, outdir):
    ch = ''
    for it in items:
        ch += ('<item><title>' + html.escape(it['title']) + '</title>'
         '<link>' + SITE_DOMAIN + news_slug_page(it) + '</link>'
         '<guid>' + SITE_DOMAIN + news_slug_page(it) + '</guid>'
         '<pubDate>' + it['date'] + 'T09:00:00+03:00</pubDate>'
         '<description>' + html.escape(it.get('teaser') or '') + '</description></item>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
     '<title>' + SITE_NAME + ' — новости EV в России</title><link>' + SITE_DOMAIN + '/news/</link>'
     '<description>Практика владения электромобилем в России: цифры, зима, зарядка, аксессуары</description><language>ru</language>' + ch + '</channel></rss>')
    with open(os.path.join(outdir,'feed.xml'),'w',encoding='utf-8') as f: f.write(xml)

# ================= КАРТА ЗАРЯДНЫХ СТАНЦИЙ =================
CITIES = [
 ('Москва','55.62,37.28,56.05,38.05'),('Санкт-Петербург','59.75,30.05,60.12,30.62'),
 ('Нижний Новгород','56.18,43.74,56.40,44.10'),('Екатеринбург','56.72,60.48,56.94,60.75'),
 ('Новосибирск','54.94,82.80,55.10,83.10'),('Казань','55.70,49.05,55.90,49.28'),
 ('Краснодар','44.95,38.88,45.10,39.08'),('Ростов-на-Дону','47.16,39.60,47.32,39.82'),
 ('Сочи','43.50,39.60,43.68,39.85'),('Владивосток','43.05,131.80,43.24,132.05'),
 ('Симферополь','44.88,34.05,45.00,34.20'),('Минск','53.82,27.44,53.98,27.66'),
 ('Алматы','43.17,76.80,43.32,76.99')]

def map_page(outdir):
    city_btns = ''.join('<button class="cbtn" data-bbox="' + bb + '">' + c + '</button>' for c,bb in CITIES)
    body = ('<div class="hero"><div class="kicker">Карта</div><h1>Зарядные станции рядом</h1>'
     '<p class="lede">Живая карта зарядной инфраструктуры по данным OpenStreetMap. Выберите город — покажем станции, операторов и разъёмы.</p></div>'
     '<div class="cbtns">' + city_btns + '</div>'
     '<div id="map" class="nmap"></div>'
     '<p class="note" id="mstat">Загрузка данных…</p>'
     '<h2>Как пользоваться картой</h2>'
     '<div class="card"><p>Данные — открытая база OpenStreetMap: зарядки размечают сами пользователи, покрытие в мегаполисах хорошее, в малых городах — частичное. '
     'Станция кликабельна: покажет оператора и типы разъёмов, если они указаны в данных.</p>'
     '<p class="note">Не видите станцию, которая есть в реальности? Её можно добавить в OSM за пару минут — база открытая.</p></div>'
     '<p class="note">Данные © участники <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> (ODbL). Запросы через Overpass API.</p>'
     '<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Подобрать комплект зарядки</a><a class="btn ghost" href="/pains.html">Проблемы и решения</a></div>'
     '<link rel="stylesheet" href="/assets/leaflet/leaflet.css">'
     '<script src="/assets/leaflet/leaflet.js"></script>'
     '<script>'
     'var map=L.map("map").setView([55.75,37.6],10);'
     'L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap"}).addTo(map);'
     'var markers=[];'
     'function clearM(){markers.forEach(function(m){map.removeLayer(m)});markers=[];}'
     'function loadBbox(bbox){var p=bbox.split(",");clearM();document.getElementById("mstat").textContent="Загрузка…";'
     'map.fitBounds([[p[0],p[1]],[p[2],p[3]]]);'
     'var q="[out:json][timeout:25];node[amenity=charging_station]("+bbox+");out tags center 400;";'
     'fetch("https://overpass-api.de/api/interpreter",{method:"POST",body:"data="+encodeURIComponent(q)})'
     '.then(function(r){return r.json()})'
     '.then(function(d){var els=d.elements||[];els.forEach(function(e){var la=e.lat,lo=e.lon;if(!la&&e.center){la=e.center.lat;lo=e.center.lon}if(la==null)return;'
     'var t=e.tags||{};var nm=t.operator||t.name||"Зарядная станция";var sk=[];for(var k in t){if(k.indexOf("socket:")===0&&t[k]!=="no")sk.push(k.replace("socket:",""))}'
     'var txt="<b>"+nm+"</b>"+(sk.length?"<br>Разъёмы: "+sk.join(", "):"");'
     'var m=L.marker([la,lo]).addTo(map).bindPopup(txt);markers.push(m);});'
     'document.getElementById("mstat").textContent=els.length?("Найдено станций: "+els.length):("В этой области OpenStreetMap пока нет размеченных зарядок — добавьте их, это открытая база");})'
     '.catch(function(){document.getElementById("mstat").textContent="Не удалось загрузить данные Overpass — попробуйте ещё раз через минуту";});}'
     'document.querySelectorAll(".cbtn").forEach(function(b){b.addEventListener("click",function(){loadBbox(b.dataset.bbox)})});'
     'loadBbox("' + CITIES[0][1] + '");'
     '</script>')
    write_page(os.path.join(outdir,'charging','index.html'), 'Карта зарядных станций для электромобилей | Запас хода',
        'Живая карта зарядных станций по данным OpenStreetMap: Москва, Санкт-Петербург, Екатеринбург, Казань и другие города. Операторы и разъёмы.',
        body, '/charging/')

def map_page(outdir):
    city_btns = ''.join('<button class="cbtn" data-bbox="' + bb + '">' + c + '</button>' for c,bb in CITIES)
    body = ('<div class="hero"><div class="kicker">Карта</div><h1>Зарядные станции рядом</h1>'
     '<p class="lede">Живая карта зарядной инфраструктуры по данным OpenStreetMap. Выберите город — покажем станции, операторов и разъёмы.</p></div>'
     '<div class="cbtns">' + city_btns + '</div>'
     '<div id="map" class="nmap"></div>'
     '<p class="note" id="mstat">Загрузка данных…</p>'
     '<h2>Как пользоваться картой</h2>'
     '<div class="card"><p>Данные — открытая база OpenStreetMap: зарядки размечают сами пользователи, покрытие в мегаполисах хорошее, в малых городах — частичное. '
     'Станция кликабельна: покажет оператора и типы разъёмов, если они указаны в данных.</p>'
     '<p class="note">Не видите станцию, которая есть в реальности? Её можно добавить в OSM за пару минут — база открытая.</p></div>'
     '<p class="note">Данные © участники <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> (ODbL). Запросы через Overpass API.</p>'
     '<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Подобрать комплект зарядки</a><a class="btn ghost" href="/pains.html">Проблемы и решения</a></div>'
     '<link rel="stylesheet" href="/assets/leaflet/leaflet.css">'
     '<script src="/assets/leaflet/leaflet.js"></script>'
     '<script>'
     'var map=L.map("map").setView([55.75,37.6],10);'
     'L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap"}).addTo(map);'
     'var markers=[];'
     'function clearM(){markers.forEach(function(m){map.removeLayer(m)});markers=[];}'
     'function loadBbox(bbox){var p=bbox.split(",");clearM();document.getElementById("mstat").textContent="Загрузка…";'
     'map.fitBounds([[p[0],p[1]],[p[2],p[3]]]);'
     'var q="[out:json][timeout:25];node[amenity=charging_station]("+bbox+");out tags center 400;";'
     'fetch("https://overpass-api.de/api/interpreter",{method:"POST",body:"data="+encodeURIComponent(q)})'
     '.then(function(r){return r.json()})'
     '.then(function(d){var els=d.elements||[];els.forEach(function(e){var la=e.lat,lo=e.lon;if(!la&&e.center){la=e.center.lat;lo=e.center.lon}if(la==null)return;'
     'var t=e.tags||{};var nm=t.operator||t.name||"Зарядная станция";var sk=[];for(var k in t){if(k.indexOf("socket:")===0&&t[k]!=="no")sk.push(k.replace("socket:",""))}'
     'var txt="<b>"+nm+"</b>"+(sk.length?"<br>Разъёмы: "+sk.join(", "):"");'
     'var m=L.marker([la,lo]).addTo(map).bindPopup(txt);markers.push(m);});'
     'document.getElementById("mstat").textContent=els.length?("Найдено станций: "+els.length):("В этой области OpenStreetMap пока нет размеченных зарядок — добавьте их, это открытая база");})'
     '.catch(function(){document.getElementById("mstat").textContent="Не удалось загрузить данные Overpass — попробуйте ещё раз через минуту";});}'
     'document.querySelectorAll(".cbtn").forEach(function(b){b.addEventListener("click",function(){loadBbox(b.dataset.bbox)})});'
     'loadBbox("' + CITIES[0][1] + '");'
     '</script>')
    write_page(os.path.join(outdir,'charging','index.html'), 'Карта зарядных станций для электромобилей | Запас хода',
        'Живая карта зарядных станций по данным OpenStreetMap: Москва, Санкт-Петербург, Екатеринбург, Казань и другие города. Операторы и разъёмы.',
        body, '/charging/')

# ================= ПОИСК =================
def search_page(outdir, index_items):
    js = json.dumps(index_items, ensure_ascii=False)
    body = ('<div class="hero"><div class="kicker">Поиск</div><h1>Поиск по справочнику</h1>'
     '<p class="lede">Модели, проблемы, новости и VIN — всё в одном поиске.</p></div>'
     '<input class="search" id="q" placeholder="Например: Zeekr, адаптер, зимой, VIN…">'
     '<div id="res"></div>'
     '<script>var IDX=' + js + ';'
     'document.getElementById("q").addEventListener("input",function(){var q=this.value.toLowerCase().trim();var out="";'
     'if(q){var hits=IDX.filter(function(x){return (x.t+" "+x.d).toLowerCase().indexOf(q)>=0}).slice(0,40);'
     'out=hits.map(function(x){return "<a class=mcard href="+x.u+"><b>"+x.t+"</b><span>"+x.d+"</span></a>"}).join("");'
     'if(!hits.length)out="<p class=note>Ничего не нашлось. Попробуйте другое слово.</p>";}'
     'document.getElementById("res").innerHTML=out;});</script>')
    write_page(os.path.join(outdir,'search.html'), 'Поиск | Запас хода',
        'Поиск по 137 моделям, руководствам, новостям и VIN-справочнику.', body, '/search.html')

# ================= LLMS.TXT =================
def llms_files(outdir, news):
    canon = [
      ('Каталог моделей', '/index.html', '137 моделей EV в РФ: разъёмы, мощности, боли, решения'),
      ('Руководства по проблемам', '/pains.html', '12 практических руководств с решениями'),
      ('Новости', '/news/', 'Лента: цифры, зима, зарядка, новые модели'),
      ('Карта зарядных станций', '/charging/', 'Зарядные станции по данным OpenStreetMap'),
      ('VIN-справочник', '/vin/', 'Структура VIN, коды года, проверка истории для EV в РФ'),
      ('О проекте', '/about.html', 'Методика и источники справочника'),
    ]
    txt = '# ' + SITE_NAME + '\n\n> Практика владения электромобилем в России: разъёмы зарядки (GB/T, Type 2/CCS2, Type 1/CCS1, CHAdeMO), зимняя эксплуатация, реальные расходы, VIN-проверка параллельного импорта. База: 137 моделей 2019–2026, ввезённых в РФ. Мини-приложение с каталогом аксессуаров: https://t.me/zapashoda_ev_bot/app\n\n'
    txt += '## Разделы\n\n'
    for t,u,d in canon: txt += '- [' + t + '](' + SITE_DOMAIN + u + '): ' + d + '\n'
    txt += '\n## Популярные модели\n\n'
    pop = ['Zeekr 001','Zeekr 007','Zeekr 7X','Li Auto L6','Voyah Free','Avatr 11','Xiaomi SU7','BYD Song Plus EV','BYD Yuan Plus','Geely EX5','Geely Galaxy E5','Deepal S07','Evolute i-Jet','Moskvich 3e','Tesla Model 3','VW ID.3','BMW i4','Nissan Leaf']
    seen = set()
    for pn in pop:
        hit = [m for m in MODELS if pn.lower() in (m['brand']+' '+m['model']).lower()]
        if hit and hit[0]['model'] not in seen:
            m = hit[0]; seen.add(m['model'])
            txt += '- [' + m['brand'] + ' ' + m['model'] + '](' + SITE_DOMAIN + '/models/' + slug(m['brand']) + '-' + slug(m['model']) + '.html): разъёмы ' + str(m.get('ac') or '?') + ' / ' + str(m.get('dc') or '?') + '\n'
    txt += '\n## Руководства по проблемам\n\n'
    for sl,t,d,_ in PAIN_ARTICLES: txt += '- [' + t + '](' + SITE_DOMAIN + '/pain/' + sl + '.html): ' + d + '\n'
    if news:
        txt += '\n## Свежие новости\n\n'
        for it in news[:20]: txt += '- [' + it['title'] + '](' + SITE_DOMAIN + news_slug_page(it) + '): ' + (it.get('teaser') or '') + '\n'
    with open(os.path.join(outdir,'llms.txt'),'w',encoding='utf-8') as f: f.write(txt)

    full = txt + '\n\n# ПОЛНЫЙ ТЕКСТ РУКОВОДСТВ\n\n'
    for sl,t,d,pids in PAIN_ARTICLES:
        full += '## ' + t + '\n\n' + d + '\n\n'
        for i in pids:
            p = PAINS[i]
            full += '### ' + p['pain'] + ' [' + i + ']\nКому: ' + p['who'] + '\nРешение: ' + p['sol'] + '\n' + src_html(p).replace('<a href="','( ').replace('</a>',' )').replace('Источники: ','Источники: ') + '\n\n'
    full += '# МОДЕЛИ: РАЗЪЁМЫ\n\n'
    for m in MODELS:
        full += '## ' + m['brand'] + ' ' + m['model'] + ' (' + m['years'] + ', ' + m['type'] + ', ' + m['market'] + ')\n'
        full += 'AC: ' + str(m.get('ac') or '—') + ' | DC: ' + str(m.get('dc') or '—') + ' | OBC: ' + str(m.get('obc') or '—') + ' | DC-мощность: ' + str(m.get('dcp') or '—') + '\n'
        if m.get('sol'): full += 'Для зарядки: ' + str(m['sol']) + '\n'
        full += '\n'
    if news:
        full += '# НОВОСТИ\n\n'
        for it in news:
            full += '## ' + it['title'] + ' (' + it['date'] + ')\n' + (it.get('teaser') or '') + '\n\n' + it['body'].replace('</p><p>','\n\n').replace('<p>','').replace('</p>','') + '\n\n'
    with open(os.path.join(outdir,'llms-full.txt'),'w',encoding='utf-8') as f: f.write(full)

# ================= OG-КАРТОЧКИ (PIL) =================
def og_gen(outdir, jobs):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print('PIL недоступен — OG-карточки пропущены'); return
    here = os.path.dirname(os.path.abspath(__file__))
    fb = os.path.join(here, 'assets', 'fonts', 'DejaVuSans-Bold.ttf')
    if not os.path.exists(fb):
        fb = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    if not os.path.exists(fb):
        print('Шрифт не найден — OG пропущены'); return
    f_big = ImageFont.truetype(fb, 62); f_small = ImageFont.truetype(fb, 30); f_url = ImageFont.truetype(fb, 26)
    ogdir = os.path.join(outdir, 'assets', 'og')
    os.makedirs(ogdir, exist_ok=True)
    LIME = (245, 245, 247); DARK = (29, 29, 31); MUT = (142, 142, 147); DEC = (214, 214, 222)
    for rel, title in jobs:
        img = Image.new('RGB', (1200, 630), LIME)
        dr = ImageDraw.Draw(img)
        dr.polygon([(1060, 60), (940, 230), (1020, 230), (970, 400), (1120, 190), (1030, 190), (1090, 60)], fill=DEC)
        words = title.split()
        lines = []; cur = ''
        for w in words:
            t = (cur + ' ' + w).strip()
            if dr.textlength(t, font=f_big) > 1020 and cur:
                lines.append(cur); cur = w
            else:
                cur = t
        if cur: lines.append(cur)
        lines = lines[:4]
        y = 250
        for ln in lines:
            dr.text((60, y), ln, font=f_big, fill=DARK); y += 74
        dr.text((60, 520), 'ЗАПАС ХОДА · ПРАКТИКА EV В РОССИИ', font=f_small, fill=DARK)
        dr.text((60, 566), SITE_DOMAIN.replace('https://','').replace('http://',''), font=f_url, fill=MUT)
        p = os.path.join(outdir, rel.lstrip('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        img.save(p, 'PNG', optimize=True)
    print('OG-карточек:', len(jobs))

# ================= ГЛАВНАЯ, ПРОЧИЕ, SITEMAP =================
def home_page(outdir):
    art_cards = ''.join('<a class="mcard" href="/pain/'+sl+'.html"><b>'+html.escape(title)+'</b><span>'+html.escape(desc)+'</span></a>' for sl,title,desc,pids in PAIN_ARTICLES)
    pop_names = ['Zeekr 001','Zeekr 007','Zeekr 7X','Li Auto L6','Voyah Free','Avatr 11','Xiaomi SU7','Changan Qiyuan A05','BYD Song Plus EV','BYD Yuan Plus','Geely EX5','Geely Galaxy E5','Deepal S07','Evolute i-Jet','Moskvich 3e','Tesla Model 3','VW ID.3','BMW i4','Nissan Leaf']
    pop_cards = ''
    for pn in pop_names:
        hit = [m for m in MODELS if pn.lower() in (m['brand']+' '+m['model']).lower()]
        if hit:
            m = hit[0]
            pop_cards += '<a class="mcard" href="/models/'+slug(m["brand"])+'-'+slug(m["model"])+'.html"><b>'+html.escape(m["brand"]+" "+m["model"])+'</b><span>'+m["years"]+' · '+m["type"]+' · '+m["freq"]+' ввоз</span></a>'
    model_cards = ''.join('<a class="mcard" href="/models/'+slug(m["brand"])+'-'+slug(m["model"])+'.html"><b>'+html.escape(m["brand"]+" "+m["model"])+'</b><span>'+m["years"]+' · '+m["type"]+' · '+m["freq"]+' ввоз</span></a>' for m in sorted(MODELS, key=lambda x:(x['freq']!='Массовый', x['brand'], x['model'])))
    body = ('<div class="hero"><div class="kicker">Справочник</div>'
     '<h1>Как зарядить и чем лечить ваш электромобиль</h1>'
     '<p class="lede">Разъёмы, реальные проблемы и проверенные решения для 137 моделей, ввезённых в Россию в 2019–2026: GB/T, Type 2/CCS2, Type 1/CCS1, CHAdeMO.</p>'
     '<div class="ctas"><a class="btn lime" href="' + TG_BOT_APP + '">Открыть каталог аксессуаров</a><a class="btn ghost" href="/news/">Читать новости</a></div></div>'
     '<input class="search" id="q" placeholder="Начните вводить марку или модель: Zeekr, BYD, Leaf…">'
     '<h2>Частые проблемы — быстрые ответы</h2><div class="grid">' + art_cards + '</div>'
     '<h2>Популярные модели</h2><p class="note">Разъёмы, мощность и решения по самым массовым машинам в РФ.</p><div class="grid">' + pop_cards + '</div>'
     '<h2 id="models-list">Все модели</h2><div class="grid">' + model_cards + '</div>'
     '<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Каталог в мини-приложении</a><a class="btn ghost" href="' + TG_CHANNEL + '">Канал «Запас хода»</a><a class="btn ghost" href="/charging/">Карта зарядных станций</a><a class="btn ghost share" href="#" onclick="sharePg();return false;">Поделиться</a></div>'
     '<script>document.getElementById("q").addEventListener("input",function(){var q=this.value.toLowerCase();'
     'document.querySelectorAll(".grid .mcard").forEach(function(c){c.style.display=c.textContent.toLowerCase().indexOf(q)>=0?"":"none"});});</script>')
    write_page(os.path.join(outdir,'index.html'), 'Запас хода — разъёмы зарядки, боли и решения для 137 моделей EV в России',
        'Справочник: какой разъём зарядки у Zeekr, BYD, Voyah, Li Auto, Leaf и 130+ других моделей, типичные проблемы владельцев и решения, карта ЗУ и VIN-проверка.',
        body, '/')

def pains_index(outdir):
    arts = ''.join('<a class="mcard" href="/pain/'+sl+'.html"><b>'+title+'</b><span>'+desc+'</span></a>' for sl,title,desc,pids in PAIN_ARTICLES)
    write_page(os.path.join(outdir,'pains.html'), 'Проблемы и решения электромобилей | Запас хода',
        'Не заряжается, подогрев батареи, зарядка от розетки, адаптеры GB/T и CCS2, кабель не отдаёт, 12В АКБ, CHAdeMO — решения с источниками.',
        '<h1>Типичные проблемы электромобилей и их решения</h1><p class="lede">Руководства по самым частым болям владельцев — со ссылками на первоисточники.</p><div class="grid">'+arts+'</div>', '/pains.html')

def pain_article_page(sl, title, desc, pids, outdir):
    rel_html = ', '.join('<a href="/models/'+slug(m["brand"])+'-'+slug(m["model"])+'.html">'+html.escape(m["brand"]+" "+m["model"])+'</a>' for m in rel_models(RELATED.get(sl,[])))
    blocks = ''.join('<div class="card"><span class="pain-id">'+i+'</span><h3>'+html.escape(PAINS[i]["pain"])+'</h3><div class="sol"><b>Решение:</b> '+html.escape(PAINS[i]["sol"])+'</div><p class="src">'+src_html(PAINS[i])+'</p></div>' for i in pids)
    body = '<h1>'+title+'</h1><p class="lede">'+desc+'</p>'+blocks+'<h2>Связанные модели</h2><p class="note">Разъёмы и боли конкретных моделей: '+rel_html+'. Полный каталог — <a href="/index.html">по ссылке</a>.</p><div class="cta"><a class="btn lime" href="'+TG_BOT_APP+'">Подобрать комплект</a><a class="btn ghost" href="'+TG_CHANNEL+'">Канал «Запас хода»</a><a class="btn ghost share" href="#" onclick="sharePg();return false;">Поделиться</a></div>'
    write_page(os.path.join(outdir,'pain', sl+'.html'), title+' | Запас хода', 'Практическое руководство: '+desc, body, '/pain/'+sl+'.html')

def rel_models(rel_brands):
    out = []
    for b in rel_brands:
        ms = [m for m in MODELS if m['brand'].strip()==b and m['freq']=='Массовый'] or [m for m in MODELS if m['brand'].strip()==b]
        for m in ms[:1]: out.append(m)
    return out[:4]

def about_page(outdir, news):
    n = len(news)
    write_page(os.path.join(outdir,'about.html'), 'О проекте «Запас хода»', 'Как устроен справочник владения электромобилем: источники, методика, кто делает.',
        '<h1>О проекте</h1><p class="lede">«Запас хода» — независимый справочник по практике владения электромобилем в России.</p>'
        '<p>База: 137 моделей с типами подключения, реальные боли владельцев с форумов (Drive2, chinamobil, клубы брендов) и профильных сервисов. Каждое решение снабжено ссылкой на первоисточник. Карта зарядных станций — данные OpenStreetMap (ODbL).</p>'
        '<p>Также у нас: Telegram-канал <a href="'+TG_CHANNEL+'">@zapashoda_ev</a> и мини-приложение с каталогом аксессуаров (<a href="'+TG_BOT_APP+'">открыть</a>). Новостей в ленте на момент сборки: '+str(n)+'.</p>'
        '<p class="note">Проект ведёт поставщик зарядных комплектов для китайских и европейских EV: подбор, доставка по РФ, консультация.</p>', '/about.html')

def vin_hub(outdir):
    pop_first = ['Zeekr','Li Auto','BYD','Voyah','Avatr','Tesla','VW','BMW','Kia','Hyundai','Nissan','Xiaomi','Geely','Hongqi','Evolute','Moskvich','Audi','Mercedes','Skoda','MG']
    brands = sorted(VIN_BRANDS, key=lambda b: pop_first.index(b) if b in pop_first else 999)
    cards = ''.join('<a class="mcard" href="/vin/'+slug(b)+'.html"><b>VIN '+html.escape(b)+'</b><span>'+html.escape(VIN_BRANDS[b][0])+' · код года, табличка, проверка</span></a>' for b in brands)
    body = ('<div class="hero"><div class="kicker">VIN-справочник</div><h1>VIN электромобиля: расшифровка и проверка</h1>'
     '<p class="lede">17 символов, которые говорят о машине всё: код завода, модельный год, серийник. Для владельцев EV в России — с акцентом на параллельный импорт.</p></div>'
     + VIN_STRUCT +
     '<h2>VIN по брендам</h2><div class="grid2">' + cards + '</div>'
     '<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Подобрать комплект зарядки</a><a class="btn ghost" href="/news/">Новости</a></div>')
    write_page(os.path.join(outdir,'vin','index.html'), 'VIN-справочник электромобилей: расшифровка, код года, проверка | Запас хода',
        'Как расшифровать VIN электромобиля: структура, коды модельного года, где находится табличка, бесплатная проверка ГИБДД и ЭПТС/СБКТС для параллельного импорта.',
        body, '/vin/')

def misc_pages(outdir):
    with open(os.path.join(outdir,'robots.txt'),'w',encoding='utf-8') as f:
        f.write('User-agent: *\nAllow: /\nSitemap: '+SITE_DOMAIN+'/sitemap.xml\n')
    with open(os.path.join(outdir,'.nojekyll'),'w') as f: f.write('')
    body = '<h1>Страница не найдена</h1><p class="lede">Такой страницы нет — возможно, ссылка устарела.</p><div class="cta"><a class="btn lime" href="/index.html">На главную</a><a class="btn ghost" href="/news/">Новости</a></div>'
    write_page(os.path.join(outdir,'404.html'), '404 — страница не найдена | Запас хода', 'Страница не найдена.', body, '/404.html')

def build_sitemap(slugs_model, news, vin_slugs):
    urls = [SITE_DOMAIN+'/', SITE_DOMAIN+'/pains.html', SITE_DOMAIN+'/about.html', SITE_DOMAIN+'/news/',
            SITE_DOMAIN+'/charging/', SITE_DOMAIN+'/vin/', SITE_DOMAIN+'/search.html']
    urls += [SITE_DOMAIN+'/'+s.replace('.html','') for s in slugs_model]
    urls += [SITE_DOMAIN+'/pain/'+s+'.html' for s,_,_,_ in PAIN_ARTICLES]
    urls += [SITE_DOMAIN+news_slug_page(it) for it in news]
    urls += [SITE_DOMAIN+'/'+s.replace('.html','') for s in vin_slugs]
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>'+u+'</loc></url>' for u in urls) + '</urlset>'

def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else '_site'
    repo_root = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(repo_root, 'data')
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(os.path.join(outdir,'assets'), exist_ok=True)
    LOGO = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1d1d1f"/><path d="M37 8 L16 38 h14 l-5 18 25-34 H34 l8-14 z" fill="#ffffff"/></svg>'
    with open(os.path.join(outdir,'assets','logo.svg'),'w',encoding='utf-8') as f: f.write(LOGO)
    with open(os.path.join(outdir,'style.css'),'w',encoding='utf-8') as f: f.write(CSS)
    # leaflet
    lf = os.path.join(repo_root,'static','leaflet')
    if os.path.isdir(lf):
        dst = os.path.join(outdir,'assets','leaflet')
        if os.path.isdir(dst): shutil.rmtree(dst)
        shutil.copytree(lf, dst)
    news = load_news(data_dir)
    news_map = load_news_map(data_dir)
    print('Новостей в базе:', len(news))
    home_page(outdir)
    pains_index(outdir)
    slugs = [model_page(m, outdir) for m in MODELS]
    for sl,title,desc,pids in PAIN_ARTICLES:
        pain_article_page(sl,title,desc,pids,outdir)
    for it in news:
        news_page(it, outdir, news_map)
    news_index(news, outdir)
    news_feed(news, outdir)
    vin_slugs = []
    for brand in sorted(VIN_BRANDS):
        if brand in [m['brand'].strip() for m in MODELS] or True:
            vin_slugs.append(vin_brand_page(brand, outdir))
    vin_hub(outdir)
    map_page(outdir)
    idx = []
    for m in MODELS:
        idx.append({'t': m['brand']+' '+m['model'], 'd': 'Разъёмы: '+str(m.get('ac') or '—')+' / '+str(m.get('dc') or '—')+' · '+m['type']+' · '+m['market'], 'u': '/models/'+slug(m['brand'])+'-'+slug(m['model'])+'.html'})
    for sl,title,desc,_ in PAIN_ARTICLES:
        idx.append({'t': title, 'd': desc, 'u': '/pain/'+sl+'.html'})
    for it in news:
        idx.append({'t': it['title'], 'd': it.get('teaser') or '', 'u': news_slug_page(it)})
    for brand in VIN_BRANDS:
        idx.append({'t': 'VIN '+brand, 'd': 'Расшифровка VIN, код года, проверка истории ('+VIN_BRANDS[brand][0]+')', 'u': '/vin/'+slug(brand)+'.html'})
    for t,u,d in [('/', 'Запас хода', 'Справочник по зарядке EV в России'), ('/charging/','Карта зарядных станций','ЗУ по данным OSM'), ('/pains.html','Проблемы и решения','12 руководств')]:
        idx.append({'t': t, 'd': d, 'u': u})
    search_page(outdir, idx)
    llms_files(outdir, news)
    about_page(outdir, news)
    misc_pages(outdir)
    # OG-карточки: новости + бренды VIN + дефолт
    jobs = [('/assets/og/default.png', 'Запас хода — практика владения электромобилем в России')]
    for it in news:
        jobs.append(('/assets/og/n-'+it['date']+'-'+it['slug']+'.png', it['title']))
    for brand in VIN_BRANDS:
        jobs.append(('/assets/og/vin-'+slug(brand)+'.png', 'VIN '+brand+': расшифровка и проверка истории'))
    for sl,title,_,_ in PAIN_ARTICLES:
        jobs.append(('/assets/og/p-'+sl+'.png', title))
    og_gen(outdir, jobs)
    # OG для моделей (137) — упрощённые (заголовок покороче)
    for m in MODELS:
        jobs.append(('/assets/og/m-'+slug(m['brand'])+'-'+slug(m['model'])+'.png', m['brand']+' '+m['model']+' — разъёмы зарядки'))
    og_gen(outdir, jobs)
    with open(os.path.join(outdir,'sitemap.xml'),'w',encoding='utf-8') as f: f.write(build_sitemap(slugs, news, vin_slugs))
    total = sum(len(fs) for _,_,fs in os.walk(outdir))
    print('Готово: моделей', len(slugs), '| новостей', len(news), '| VIN-страниц', len(vin_slugs), '| файлов в _site:', total)

if __name__ == '__main__':
    main()

"""
PCMC.m sorrol sorra huseg (fidelity) portja Pythonra.

Szandekosan koveti a MATLAB eredetit:
- globalis valtozok (M, indexi, indexj, HianyzoElemek, ...)
- fminbound (= MATLAB fminbnd, xtol=1e-4 alapertelmezessel)
- inv(L) @ RHS explicit invertalassal
- det(L) == 0 osszefuggoseg-ellenorzes
- max(eig(M)) es sajatvektor-oszlop kereses az eredeti logikaval
"""

import numpy as np
from scipy.optimize import fminbound

# --- globalis valtozok, mint a MATLAB-ban ---
M = None
indexi = None
indexj = None
HianyzoElemek = None
HianyzoElemekSzama = None
A = None


def EgyvaltozosFuggveny(t):
    global M, indexi, indexj
    B = M.copy()
    B[indexi, indexj] = np.exp(t)
    B[indexj, indexi] = np.exp(-t)
    # MATLAB max(eig(B)): komplexre a legnagyobb abszolut erteku elem
    ev = np.linalg.eigvals(B)
    return ev[np.argmax(np.abs(ev))].real


def main():
    global M, indexi, indexj, HianyzoElemek, HianyzoElemekSzama, A

    atlagoslambdamax = {3: 4.049, 4: 6.652, 5: 9.435, 6: 12.245,
                        7: 15.045, 8: 17.830, 9: 20.605, 10: 23.373}

    A = np.array([
        [1,   5,   3,   7,   6,   6,   1/3, 1/4],
        [0,   1,   0,   5,   0,   3,   0,   1/7],
        [0,   0,   1,   0,   3,   0,   6,   0],
        [0,   0,   0,   1,   0,   1/4, 0,   1/8],
        [0,   0,   0,   0,   1,   0,   1/5, 0],
        [0,   0,   0,   0,   0,   1,   0,   1/6],
        [0,   0,   0,   0,   0,   0,   1,   0],
        [0,   0,   0,   0,   0,   0,   0,   1],
    ], dtype=float)

    matrixmeret = max(A.shape)
    for indexi in range(matrixmeret):
        for indexj in range(matrixmeret):
            if A[indexi, indexj] == 0:
                pass
            else:
                A[indexj, indexi] = 1 / A[indexi, indexj]

    print('A nem teljesen kitoltott paros osszehasonlitas matrix '
          '(a hianyzo elemeket 0-k jelolik):')
    print(A)

    M = A.copy()
    matrixmeret = max(M.shape)

    L = np.zeros((matrixmeret - 1, matrixmeret - 1))

    for indexi in range(matrixmeret - 1):
        Degree = matrixmeret - 1
        for indexj in range(matrixmeret):
            if M[indexi, indexj] == 0:
                Degree = Degree - 1
        L[indexi, indexi] = Degree

    for indexi in range(matrixmeret - 2):
        for indexj in range(indexi + 1, matrixmeret - 1):
            if M[indexi, indexj] == 0:
                pass
            else:
                L[indexi, indexj] = -1
                L[indexj, indexi] = -1

    if np.linalg.det(L) == 0:
        print('A graf meg nem osszefuggo. Irjon be tovabbi elemeket!')
        return None
    else:
        RHS = np.zeros((matrixmeret - 1, 1))
        for indexj in range(matrixmeret - 1):
            ColumnProduct = 1
            for indexi in range(matrixmeret):
                if M[indexi, indexj] == 0:
                    M[indexi, indexj] = 1
                ColumnProduct = ColumnProduct * M[indexi, indexj]
            RHS[indexj, 0] = -np.log(ColumnProduct)

        y = np.linalg.inv(L) @ RHS          # inv(L)*RHS, mint az eredetiben
        w = np.exp(y).flatten()
        w = np.append(w, 1)
        wLLSM = w / np.sum(w)
        print('Az LLSM sulyvektor w1+w2+...+wn = 1 normalizalassal:')
        print(wLLSM)

        M = A.copy()

        HianyzoElemekSzama = 0
        HianyzoElemek = []
        for indexi in range(matrixmeret - 1):
            for indexj in range(indexi + 1, matrixmeret):
                if M[indexi, indexj] == 0:
                    HianyzoElemekSzama += 1
                    HianyzoElemek.append((indexi, indexj))

        if HianyzoElemekSzama == 0:
            D, V = np.linalg.eig(M)
            lambdamax = np.max(np.abs(D))
            CR = (lambdamax - matrixmeret) / \
                 (atlagoslambdamax[matrixmeret] - matrixmeret)
            melyik = 0
            for ind in range(matrixmeret):
                if abs(lambdamax - D[ind]) < 1e-4:
                    melyik = ind
            EM = np.abs(V[:, melyik])
            wEM = EM / np.sum(EM)
            print('A matrix teljesen ki van toltve. CR erteke:')
            print(CR)
            print('jobboldali sajatvektor:')
            print(wEM)
            print('lambdamax=')
            print(lambdamax)
            return {'wLLSM': wLLSM, 'wEM': wEM, 'CR': CR,
                    'lambdamax': lambdamax, 'M': M}
        else:
            # *****************
            M = A.copy()

            for (i, j) in HianyzoElemek:
                M[i, j] = 1
                M[j, i] = 1

            # Sorba megy es elemenkent optimalizal, 20-szor ismetelve
            for HanyszorFusson in range(20):
                for (hi, hj) in HianyzoElemek:
                    indexi = hi
                    indexj = hj
                    x = fminbound(EgyvaltozosFuggveny, -10, 10, xtol=1e-4)
                    M[indexi, indexj] = np.exp(x)
                    M[indexj, indexi] = np.exp(-x)

            U, V = np.linalg.eig(M)
            lambdamax = U[np.argmax(np.abs(U))].real
            print('CR-minimalis kitoltes (A*):')
            print(M)
            i = 0
            while abs(U[i] - lambdamax) > 1e-10:   # while U(i,i) ~= lambdamax
                i = i + 1
            wEM = (V[:, i] / np.sum(V[:, i])).real
            CR = (lambdamax - matrixmeret) / \
                 (atlagoslambdamax[matrixmeret] - matrixmeret)

            print('A minimalis CR ertek:')
            print(CR)
            print('a CR-t minimalizalo kitoltes jobboldali sajatvektora:')
            print(wEM)
            print('lambdamax*=')
            print(lambdamax)
            return {'wLLSM': wLLSM, 'wEM': wEM, 'CR': CR,
                    'lambdamax': lambdamax, 'M': M}


if __name__ == '__main__':
    main()

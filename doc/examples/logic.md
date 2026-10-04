# Logic in the terminal reader

Open this file with `md-read` or from nnn. Press `e` to see the source, `a` to
annotate, or `o` to follow the [workflow guide](../workflows.md).

## Formulas

Derivability: $\Gamma_i \vdash A \to B$.

Validity: $\Gamma \models A$.

Quantifiers and connectives: $\forall x\, (P(x) \to \neg Q(x))$.

## Two premises

$$
\infer[\land I]
  {\Gamma \vdash A \land B}
  {\Gamma \vdash A & \Gamma \vdash B}
$$

## Nested rules

$$
\infer[\to I]
  {\Gamma \vdash A \to (B \to A)}
  {\infer[\to I]
    {\Gamma,A \vdash B \to A}
    {\Gamma,A,B \vdash A}}
$$

## Axiom

$$
\infer[Ax]{A \vdash A}{}
$$

## Aligned equivalences

$$
\begin{aligned}
\neg(A\land B) &\iff \neg A\lor\neg B\\
\neg(A\lor B)  &\iff \neg A\land\neg B
\end{aligned}
$$

## Truth table

$$
\begin{array}{cc|c}
A & B & A\land B\\
\hline
0 & 0 & 0\\
0 & 1 & 0\\
1 & 0 & 0\\
1 & 1 & 1
\end{array}
$$

## Matrix

$$
\begin{bmatrix}
1 & 0\\
0 & 1
\end{bmatrix}
$$

## Unsupported notation stays visible

An unknown macro stays literal: $\myConnective{A}{B}$.

Code samples are not rendered as math:

```latex
\infer[\to E]{B}{A \to B & A}
```

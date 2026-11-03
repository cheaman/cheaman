;;; ------------------------------------------------------------------
;;; 경사치수.lsp  -  치수보조선 경사를 다른 치수에 그대로 옮긴다
;;;
;;;   명령 : RR   (긴 이름 : DIMOBLCOPY)
;;;   1) 경사가 있는 치수를 하나 찍는다
;;;   2) 같은 경사를 줄 치수들을 고른다 -> Enter
;;;   3) "옮겨도 다시 펴지지 않게 연관을 끊을까요?"  Y(기본) / N
;;;   되돌리기 : U 한 번이면 이번에 한 것이 모두 돌아간다
;;;
;;;   경사 각은 원본 치수의 "실제 치수보조선 방향"(정의점 14 -> 10)을
;;;   두 점으로 DIMEDIT 경사에 넘긴다. 각도 단위 · ANGBASE 설정과 상관없다.
;;;   선형(수평 · 수직 · 회전) 치수와 정렬 치수만 다룬다.
;;;
;;;   판 : v0.1 (2026-11-03) · 캐드 확인 전 (클라우드에서 짬 · 괄호 · 글꼴만 확인)
;;; ------------------------------------------------------------------

;; 선형(0) · 정렬(1) 치수면 그 번호, 아니면 nil
(defun dsm-obl:lintype (ed / f)
  (if (and ed (= (cdr (assoc 0 ed)) "DIMENSION"))
    (progn
      (setq f (logand (cdr (assoc 70 ed)) 7))
      (if (member f '(0 1)) f)
    )
  )
)

;; 잠긴 층에 있나
(defun dsm-obl:locked-p (ed / lay)
  (setq lay (tblsearch "LAYER" (cdr (assoc 8 ed))))
  (and lay (= 4 (logand 4 (cdr (assoc 70 lay)))))
)

;; 경사가 있나 - 치수보조선이 치수선에 직각이 아니면 경사 있음
(defun dsm-obl:sloped-p (ed / p10 p13 p14 da ea a52)
  (setq p10 (cdr (assoc 10 ed))
        p13 (cdr (assoc 13 ed))
        p14 (cdr (assoc 14 ed))
        a52 (cdr (assoc 52 ed)))
  (if (> (distance p10 p14) 1e-8)
    (progn
      (setq da (if (= (dsm-obl:lintype ed) 1)
                 (angle p13 p14)
                 (cond ((cdr (assoc 50 ed))) (0.0))
               )
            ea (angle p14 p10))
      (> (abs (cos (- ea da))) 1e-6)
    )
    ;; 치수보조선 길이가 0 이면 그룹 52 로 판단
    (and a52 (not (equal a52 0.0 1e-9)))
  )
)

;; 원본 치수의 치수보조선 방향을 두 점으로 (현재 UCS)
(defun dsm-obl:dir-pts (ed / p10 p14 a52)
  (setq p10 (cdr (assoc 10 ed))
        p14 (cdr (assoc 14 ed))
        a52 (cdr (assoc 52 ed)))
  (if (> (distance p10 p14) 1e-8)
    (list (trans p14 0 1) (trans p10 0 1))
    (list (trans p14 0 1) (trans (polar p14 (cond (a52) (0.0)) 1.0) 0 1))
  )
)

(defun c:DIMOBLCOPY (/ *error* oldce oldos undo-on es ed ss ss2 i e d
                       n-skip n-lock ans pts a)
  (defun *error* (msg)
    (if undo-on (command-s "_.UNDO" "_E"))
    (if oldos (setvar "OSMODE" oldos))
    (if oldce (setvar "CMDECHO" oldce))
    (if (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*BREAK*,*취소*"))
      (princ (strcat "\n멈춤 : " msg))
    )
    (princ)
  )

  ;; 1) 원본 치수
  (while (and (not ed)
              (setq es (entsel "\n경사가 있는 치수를 하나 찍으십시오 : ")))
    (setq ed (entget (car es)))
    (cond
      ((not (dsm-obl:lintype ed))
       (princ "\n  -> 선형 치수나 정렬 치수가 아닙니다. 다시 찍으십시오.")
       (setq ed nil))
      ((not (dsm-obl:sloped-p ed))
       (princ "\n  -> 이 치수는 경사가 없습니다. 다시 찍으십시오.")
       (setq ed nil))
    )
  )

  (cond
    ((not ed)
     (princ "\n원본 치수를 고르지 않아 그만둡니다."))

    ;; 2) 고칠 치수들
    ((not (progn
            (princ "\n같은 경사를 줄 치수들을 고르십시오 (다 골랐으면 Enter) : ")
            (setq ss (ssget '((0 . "DIMENSION"))))))
     (princ "\n고른 치수가 없어 그만둡니다."))

    (t
     (setq ss2 (ssadd) i 0 n-skip 0 n-lock 0)
     (repeat (sslength ss)
       (setq e (ssname ss i)
             d (entget e)
             i (1+ i))
       (cond
         ((not (dsm-obl:lintype d)) (setq n-skip (1+ n-skip)))
         ((dsm-obl:locked-p d)      (setq n-lock (1+ n-lock)))
         (t (ssadd e ss2))
       )
     )

     (if (= (sslength ss2) 0)
       (princ "\n경사를 줄 수 있는 치수(선형 · 정렬, 안 잠긴 층)가 없습니다.")
       (progn
         ;; 3) 연관 끊기를 먼저 묻는다
         (initget "Y N")
         (setq ans (getkword "\n옮겨도 다시 펴지지 않게 연관을 끊을까요? [Y/N] <Y> : "))
         (if (not ans) (setq ans "Y"))

         (setq pts   (dsm-obl:dir-pts ed)
               oldce (getvar "CMDECHO")
               oldos (getvar "OSMODE"))
         (setvar "CMDECHO" 0)
         (setvar "OSMODE" 0)
         (command "_.UNDO" "_BE")
         (setq undo-on t)

         (command "_.DIMEDIT" "_O" ss2 "" (car pts) (cadr pts))
         (if (= ans "Y")
           (command "_.DIMDISASSOCIATE" ss2 "")
         )

         (command "_.UNDO" "_E")
         (setq undo-on nil)
         (setvar "OSMODE" oldos)
         (setvar "CMDECHO" oldce)

         ;; 결과 알림 - 숫자로
         (setq a (angle (car pts) (cadr pts)))
         (if (>= a pi) (setq a (- a pi)))
         (princ (strcat "\n경사 줌 : " (itoa (sslength ss2)) "개"
                        " (치수보조선 각 " (angtos a 0 2) ")"))
         (if (> n-skip 0)
           (princ (strcat "\n  건너뜀 : 선형 · 정렬이 아닌 치수 " (itoa n-skip) "개")))
         (if (> n-lock 0)
           (princ (strcat "\n  건너뜀 : 잠긴 층의 치수 " (itoa n-lock) "개")))
         (princ (if (= ans "Y")
                  "\n  연관을 끊었습니다 - 옮겨도 경사가 남습니다."
                  "\n  연관은 그대로 - 붙은 선을 옮기면 다시 펴질 수 있습니다."))
         (princ "\n  되돌리기 : U 한 번")
       )
     )
    )
  )
  (princ)
)

(defun c:RR () (c:DIMOBLCOPY))

(princ "\n경사치수 v0.1 불러옴 - 명령 RR (DIMOBLCOPY)")
(princ)

--# -path=.:../../dist/alltenses

resource TestVerbCorrectionsGer = open DictGer, ResGer, Prelude in {

oper
  clean : Str =
    DictGer.besaenftigen_V.s ! VFin False (VPresInd Sg P3)
    ++ DictGer.besaenftigen_V.s ! VFin False (VImpfInd Sg P3)
    ++ DictGer.timbrieren_V.s ! VFin False (VPresInd Sg P3)
    ++ DictGer.timbrieren_V.s ! VFin False (VImpfInd Sg P3) ;
}

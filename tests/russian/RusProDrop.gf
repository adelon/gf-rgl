resource RusProDrop = open SyntaxRus, (P = ParadigmsRus), (E = ExtendRus),
  (L = LexiconRus) in {
oper
  call_V2 : V2 = P.mkV2
    (P.mkV P.imperfective P.transitive "звать" "зову" "зовёт" "6°b/c") P.accusative ;
}

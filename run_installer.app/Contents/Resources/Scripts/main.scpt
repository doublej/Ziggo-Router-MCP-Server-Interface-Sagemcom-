FasdUAS 1.101.10   ��   ��    k             l     ��  ��    %  Prompt user with three buttons     � 	 	 >   P r o m p t   u s e r   w i t h   t h r e e   b u t t o n s   
  
 l     ����  r         I    ��  
�� .sysodlogaskr        TEXT  m        �   D W h i c h   i n t e r f a c e   a r e   w e   i n s t a l l i n g ?  ��  
�� 
btns  J           m       �    N o n e .   E x i t .      m       �    I n s t a l l   C L I   ��  m       �      I n s t a l l   M C P��    �� !��
�� 
dflt ! m    	 " " � # #  I n s t a l l   M C P��    o      ���� 0 dialogresult dialogResult��  ��     $ % $ l     ��������  ��  ��   %  & ' & l     �� ( )��   ( ) # Determine which button was clicked    ) � * * F   D e t e r m i n e   w h i c h   b u t t o n   w a s   c l i c k e d '  + , + l    -���� - r     . / . n     0 1 0 1    ��
�� 
bhit 1 o    ���� 0 dialogresult dialogResult / o      ���� 0 
userchoice 
userChoice��  ��   ,  2 3 2 l     ��������  ��  ��   3  4 5 4 l     �� 6 7��   6 * $ Exit if user selected 'None. Exit.'    7 � 8 8 H   E x i t   i f   u s e r   s e l e c t e d   ' N o n e .   E x i t . ' 5  9 : 9 l   " ;���� ; Z    " < =���� < =    > ? > o    ���� 0 
userchoice 
userChoice ? m     @ @ � A A  N o n e .   E x i t . = L    ����  ��  ��  ��  ��   :  B C B l     ��������  ��  ��   C  D E D l     �� F G��   F &   Get the path to the .app bundle    G � H H @   G e t   t h e   p a t h   t o   t h e   . a p p   b u n d l e E  I J I l  # * K L M K r   # * N O N l  # ( P���� P I  # (�� Q��
�� .earsffdralis        afdr Q  f   # $��  ��  ��   O o      ���� 0 apppath appPath L   alias to the .app    M � R R $   a l i a s   t o   t h e   . a p p J  S T S l  + 2 U���� U r   + 2 V W V n   + . X Y X 1   , .��
�� 
psxp Y o   + ,���� 0 apppath appPath W o      ���� 0 appposix appPOSIX��  ��   T  Z [ Z l     ��������  ��  ��   [  \ ] \ l     �� ^ _��   ^ < 6 Get the parent directory (folder containing the .app)    _ � ` ` l   G e t   t h e   p a r e n t   d i r e c t o r y   ( f o l d e r   c o n t a i n i n g   t h e   . a p p ) ]  a b a l  3 > c���� c r   3 > d e d m   3 6 f f � g g  / e n      h i h 1   9 =��
�� 
txdl i 1   6 9��
�� 
ascr��  ��   b  j k j l  ? J l���� l r   ? J m n m n   ? F o p o 2  B F��
�� 
citm p o   ? B���� 0 appposix appPOSIX n o      ����  0 pathcomponents pathComponents��  ��   k  q r q l  K d s���� s r   K d t u t c   K ` v w v l  K \ x���� x n   K \ y z y 7  N \�� { |
�� 
cobj { m   T V����  | m   W [������ z o   K N����  0 pathcomponents pathComponents��  ��   w m   \ _��
�� 
ctxt u o      ���� 0 
parentpath 
parentPath��  ��   r  } ~ } l  e p ����  r   e p � � � m   e h � � � � �   � n      � � � 1   k o��
�� 
txdl � 1   h k��
�� 
ascr��  ��   ~  � � � l  q | ����� � r   q | � � � b   q x � � � m   q t � � � � �  / � o   t w���� 0 
parentpath 
parentPath � o      ���� "0 scriptpathposix scriptPathPOSIX��  ��   �  � � � l     ��������  ��  ��   �  � � � l     �� � ���   � 4 . Determine which script to run based on button    � � � � \   D e t e r m i n e   w h i c h   s c r i p t   t o   r u n   b a s e d   o n   b u t t o n �  � � � l  } � ����� � Z   } � � � ��� � =  } � � � � o   } ~���� 0 
userchoice 
userChoice � m   ~ � � � � � �  I n s t a l l   M C P � r   � � � � � b   � � � � � o   � ����� "0 scriptpathposix scriptPathPOSIX � m   � � � � � � � $ / . . / i n s t a l l - m c p . s h � o      ����  0 selectedscript selectedScript �  � � � =  � � � � � o   � ����� 0 
userchoice 
userChoice � m   � � � � � � �  I n s t a l l   C L I �  ��� � r   � � � � � b   � � � � � o   � ����� "0 scriptpathposix scriptPathPOSIX � m   � � � � � � � $ / . . / i n s t a l l - c l i . s h � o      ����  0 selectedscript selectedScript��  ��  ��  ��   �  � � � l     ��������  ��  ��   �  � � � l     �� � ���   � !  Build command for Terminal    � � � � 6   B u i l d   c o m m a n d   f o r   T e r m i n a l �  � � � l  � � ����� � r   � � � � � b   � � � � � b   � � � � � b   � � � � � b   � � � � � b   � � � � � m   � � � � � � �  c d   � n   � � � � � 1   � ���
�� 
strq � o   � ����� "0 scriptpathposix scriptPathPOSIX � m   � � � � � � �    & &   c h m o d   + x   � n   � � � � � 1   � ���
�� 
strq � o   � �����  0 selectedscript selectedScript � m   � � � � � � �    & &   � n   � � � � � 1   � ���
�� 
strq � o   � �����  0 selectedscript selectedScript � o      ���� "0 terminalcommand terminalCommand��  ��   �  � � � l     ��������  ��  ��   �  � � � l     �� � ���   � $  Run in Terminal interactively    � � � � <   R u n   i n   T e r m i n a l   i n t e r a c t i v e l y �  ��� � l  � � ����� � O   � � � � � k   � � � �  � � � I  � �������
�� .miscactvnull��� ��� null��  ��   �  ��� � I  � ��� ���
�� .coredoscnull��� ��� ctxt � o   � ����� "0 terminalcommand terminalCommand��  ��   � m   � � � ��                                                                                      @ alis    J  Macintosh HD               �<�*BD ����Terminal.app                                                   �����<�*        ����  
 cu             	Utilities   -/:System:Applications:Utilities:Terminal.app/     T e r m i n a l . a p p    M a c i n t o s h   H D  *System/Applications/Utilities/Terminal.app  / ��  ��  ��  ��       �� � ���   � ��
�� .aevtoappnull  �   � **** � �� ����� � ���
�� .aevtoappnull  �   � **** � k     � � �  
 � �  + � �  9 � �  I � �  S � �  a � �  j � �  q � �  } � �  � � �  � � �  � � �  �����  ��  ��   �   � * ��   �� "��������� @�~�}�|�{ f�z�y�x�w�v�u�t�s � ��r � ��q � � ��p � ��o ��n�m
�� 
btns
�� 
dflt�� 
�� .sysodlogaskr        TEXT�� 0 dialogresult dialogResult
�� 
bhit� 0 
userchoice 
userChoice
�~ .earsffdralis        afdr�} 0 apppath appPath
�| 
psxp�{ 0 appposix appPOSIX
�z 
ascr
�y 
txdl
�x 
citm�w  0 pathcomponents pathComponents
�v 
cobj�u��
�t 
ctxt�s 0 
parentpath 
parentPath�r "0 scriptpathposix scriptPathPOSIX�q  0 selectedscript selectedScript
�p 
strq�o "0 terminalcommand terminalCommand
�n .miscactvnull��� ��� null
�m .coredoscnull��� ��� ctxt�� ������mv��� E�O��,E�O��  hY hO)j E�O��,E` Oa _ a ,FO_ a -E` O_ [a \[Zk\Za 2a &E` Oa _ a ,FOa _ %E` O�a   _ a %E` Y �a    _ a !%E` Y hOa "_ a #,%a $%_ a #,%a %%_ a #,%E` &Oa ' *j (O_ &j )U ascr  ��ޭ
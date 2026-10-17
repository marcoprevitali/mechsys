000000000006a3f0 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)>:
   6a3f0:	endbr64
   6a3f4:	push   %rbp
   6a3f5:	mov    %rsp,%rbp
   6a3f8:	push   %r15
   6a3fa:	push   %r14
   6a3fc:	mov    %rdx,%r14
   6a3ff:	push   %r13
   6a401:	push   %r12
   6a403:	push   %rbx
   6a404:	mov    %rdi,%rbx
   6a407:	sub    $0xe8,%rsp
   6a40e:	mov    %esi,-0x104(%rbp)
   6a414:	mov    $0x1,%esi
   6a419:	mov    %rdx,-0x110(%rbp)
   6a420:	movsd  %xmm0,-0xe0(%rbp)
   6a428:	pxor   %xmm0,%xmm0
   6a42c:	movsd  %xmm1,-0xe8(%rbp)
   6a434:	mov    %fs:0x28,%rax
   6a43d:	mov    %rax,-0x38(%rbp)
   6a441:	xor    %eax,%eax
   6a443:	lea    -0xc0(%rbp),%rax
   6a44a:	movaps %xmm0,-0xc0(%rbp)
   6a451:	mov    %rax,%rdi
   6a454:	mov    %rax,-0xf0(%rbp)
   6a45b:	movq   $0x0,-0xb0(%rbp)
   6a466:	call   671b0 <std::vector<blitz::TinyVector<double, 3>, std::allocator<blitz::TinyVector<double, 3> > >::_M_default_append(unsigned long)>
   6a46b:	movdqu (%r14),%xmm6
   6a470:	mov    -0xc0(%rbp),%r13
   6a477:	pxor   %xmm0,%xmm0
   6a47b:	mov    $0x360,%edi
   6a480:	movq   $0x0,-0x90(%rbp)
   6a48b:	lea    -0x80(%rbp),%r15
   6a48f:	movups %xmm6,0x0(%r13)
   6a494:	mov    0x10(%r14),%rax
   6a498:	lea    -0xa0(%rbp),%r14
   6a49f:	movq   $0x0,-0x70(%rbp)
   6a4a7:	mov    %rax,0x10(%r13)
   6a4ab:	movaps %xmm6,-0x100(%rbp)
   6a4b2:	movaps %xmm0,-0xa0(%rbp)
   6a4b9:	movaps %xmm0,-0x80(%rbp)
   6a4bd:	call   10ad0 <operator new(unsigned long)@plt>
   6a4c2:	sub    $0x8,%rsp
   6a4c6:	mov    %r15,%r8
   6a4c9:	mov    %r14,%rcx
   6a4cc:	mov    %rax,%rdi
   6a4cf:	movsd  -0xe0(%rbp),%xmm0
   6a4d7:	lea    0x23b452(%rip),%r9        # 2a5930 <OrthoSys::O>
   6a4de:	mov    %rax,%r12
   6a4e1:	movapd %xmm0,%xmm4
   6a4e5:	unpcklpd %xmm4,%xmm4
   6a4e9:	movaps %xmm4,-0x100(%rbp)
   6a4f0:	push   %r9
   6a4f2:	movsd  -0xe8(%rbp),%xmm1
   6a4fa:	mov    -0xf0(%rbp),%rdx
   6a501:	mov    -0x104(%rbp),%esi
   6a507:	call   69650 <DEM::Particle::Particle(int, Array<blitz::TinyVector<double, 3> > const&, Array<Array<int> > const&, Array<Array<int> > const&, blitz::TinyVector<double, 3> const&, blitz::TinyVector<double, 3> const&, double, double)>
   6a50c:	pop    %rax
   6a50d:	mov    0x120(%rbx),%rsi
   6a514:	pop    %rdx
   6a515:	mov    %r12,-0xc8(%rbp)
   6a51c:	cmp    0x128(%rbx),%rsi
   6a523:	je     6a660 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x270>
   6a529:	mov    %r12,(%rsi)
   6a52c:	add    $0x8,%rsi
   6a530:	mov    %rsi,0x120(%rbx)
   6a537:	mov    0x120(%rbx),%rax
   6a53e:	movq   0xc08aa(%rip),%xmm0        # 12adf0 <cuda::std::ranges::__4::__cpo::swap+0x7e>
   6a546:	pxor   %xmm2,%xmm2
   6a54a:	movsd  -0xe8(%rbp),%xmm1
   6a552:	mulsd  0xc0bc6(%rip),%xmm1        # 12b120 <libcudart_static_71f028fdd4617209d54f8c1be3ec8f7a667e1384+0x30>
   6a55a:	movaps %xmm2,-0x50(%rbp)
   6a55e:	mov    %rax,%rdx
   6a561:	movaps %xmm0,-0x60(%rbp)
   6a565:	mov    -0x8(%rax),%rax
   6a569:	movdqa 0xc087f(%rip),%xmm0        # 12adf0 <cuda::std::ranges::__4::__cpo::swap+0x7e>
   6a571:	mulsd  0xc0b87(%rip),%xmm1        # 12b100 <libcudart_static_71f028fdd4617209d54f8c1be3ec8f7a667e1384+0x10>
   6a579:	sub    0x118(%rbx),%rdx
   6a580:	movups %xmm0,0x1c0(%rax)
   6a587:	pxor   %xmm0,%xmm0
   6a58b:	movsd  -0xe0(%rbp),%xmm3
   6a593:	movapd -0x100(%rbp),%xmm5
   6a59b:	movups %xmm0,0x1d0(%rax)
   6a5a2:	movsd  0xc0bee(%rip),%xmm0        # 12b198 <libcudart_static_71f028fdd4617209d54f8c1be3ec8f7a667e1384+0xa8>
   6a5aa:	mov    -0x110(%rbp),%rcx
   6a5b1:	sar    $0x3,%rdx
   6a5b5:	sub    $0x1,%rdx
   6a5b9:	mulsd  %xmm3,%xmm0
   6a5bd:	mulsd  %xmm3,%xmm1
   6a5c1:	unpcklpd %xmm1,%xmm0
   6a5c5:	mulpd  %xmm5,%xmm0
   6a5c9:	mulpd  %xmm5,%xmm0
   6a5cd:	movups %xmm0,0x290(%rax)
   6a5d4:	unpckhpd %xmm0,%xmm0
   6a5d8:	mulsd  0xc08c8(%rip),%xmm0        # 12aea8 <cuda::std::ranges::__4::__cpo::swap+0x136>
   6a5e0:	mulsd  %xmm3,%xmm0
   6a5e4:	mulsd  %xmm3,%xmm0
   6a5e8:	movapd %xmm0,%xmm1
   6a5ec:	movsd  %xmm0,0x158(%rax)
   6a5f4:	unpcklpd %xmm1,%xmm1
   6a5f8:	movups %xmm1,0x148(%rax)
   6a5ff:	movdqu (%rcx),%xmm6
   6a603:	movups %xmm6,0x28(%rax)
   6a607:	mov    0x10(%rcx),%rcx
   6a60b:	movb   $0x1,0x1c(%rax)
   6a60f:	mov    %rcx,0x38(%rax)
   6a613:	mov    %rdx,0x8(%rax)
   6a617:	movaps %xmm6,-0xe0(%rbp)
   6a61e:	movups %xmm2,0x1e0(%rax)
   6a625:	movsd  %xmm3,0x1f0(%rax)
   6a62d:	mov    -0x38(%rbp),%rax
   6a631:	sub    %fs:0x28,%rax
   6a63a:	jne    6a6b0 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x2c0>
   6a63c:	mov    -0xb0(%rbp),%rsi
   6a643:	lea    -0x28(%rbp),%rsp
   6a647:	mov    %r13,%rdi
   6a64a:	pop    %rbx
   6a64b:	pop    %r12
   6a64d:	sub    %r13,%rsi
   6a650:	pop    %r13
   6a652:	pop    %r14
   6a654:	pop    %r15
   6a656:	pop    %rbp
   6a657:	jmp    100d0 <operator delete(void*, unsigned long)@plt>
   6a65c:	nopl   0x0(%rax)
   6a660:	lea    -0xc8(%rbp),%rdx
   6a667:	lea    0x118(%rbx),%rdi
   6a66e:	call   6a260 <void std::vector<DEM::Particle*, std::allocator<DEM::Particle*> >::_M_realloc_insert<DEM::Particle* const&>(__gnu_cxx::__normal_iterator<DEM::Particle**, std::vector<DEM::Particle*, std::allocator<DEM::Particle*> > >, DEM::Particle* const&)>
   6a673:	jmp    6a537 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x147>
   6a678:	mov    $0x360,%esi
   6a67d:	mov    %r12,%rdi
   6a680:	call   100d0 <operator delete(void*, unsigned long)@plt>
   6a685:	mov    %r15,%rdi
   6a688:	call   58e20 <std::vector<Array<int>, std::allocator<Array<int> > >::~vector()>
   6a68d:	mov    %r14,%rdi
   6a690:	call   58e20 <std::vector<Array<int>, std::allocator<Array<int> > >::~vector()>
   6a695:	mov    -0xf0(%rbp),%rdi
   6a69c:	call   58df0 <std::vector<blitz::TinyVector<double, 3>, std::allocator<blitz::TinyVector<double, 3> > >::~vector()>
   6a6a1:	mov    -0x38(%rbp),%rax
   6a6a5:	sub    %fs:0x28,%rax
   6a6ae:	je     6a6d0 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x2e0>
   6a6b0:	call   10260 <__stack_chk_fail@plt>
   6a6b5:	endbr64
   6a6b9:	mov    %rax,%rbx
   6a6bc:	jmp    6a678 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x288>
   6a6be:	endbr64
   6a6c2:	mov    %rax,%rbx
   6a6c5:	jmp    6a685 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x295>
   6a6c7:	endbr64
   6a6cb:	mov    %rax,%rbx
   6a6ce:	jmp    6a695 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x2a5>
   6a6d0:	mov    %rbx,%rdi
   6a6d3:	call   105c0 <_Unwind_Resume@plt>
   6a6d8:	nopl   0x0(%rax,%rax,1)


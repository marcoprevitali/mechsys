00000000000682f0 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)>:
   682f0:	endbr64
   682f4:	push   %rbp
   682f5:	mov    %rsp,%rbp
   682f8:	push   %r15
   682fa:	push   %r14
   682fc:	mov    %rdx,%r14
   682ff:	push   %r13
   68301:	push   %r12
   68303:	push   %rbx
   68304:	mov    %rdi,%rbx
   68307:	sub    $0xe8,%rsp
   6830e:	mov    %esi,-0x104(%rbp)
   68314:	mov    $0x1,%esi
   68319:	mov    %rdx,-0x110(%rbp)
   68320:	movsd  %xmm0,-0xe0(%rbp)
   68328:	pxor   %xmm0,%xmm0
   6832c:	movsd  %xmm1,-0xe8(%rbp)
   68334:	mov    %fs:0x28,%rax
   6833d:	mov    %rax,-0x38(%rbp)
   68341:	xor    %eax,%eax
   68343:	lea    -0xc0(%rbp),%rax
   6834a:	movaps %xmm0,-0xc0(%rbp)
   68351:	mov    %rax,%rdi
   68354:	mov    %rax,-0xf0(%rbp)
   6835b:	movq   $0x0,-0xb0(%rbp)
   68366:	call   650b0 <std::vector<blitz::TinyVector<double, 3>, std::allocator<blitz::TinyVector<double, 3> > >::_M_default_append(unsigned long)>
   6836b:	movdqu (%r14),%xmm6
   68370:	mov    -0xc0(%rbp),%r13
   68377:	pxor   %xmm0,%xmm0
   6837b:	mov    $0x360,%edi
   68380:	movq   $0x0,-0x90(%rbp)
   6838b:	lea    -0x80(%rbp),%r15
   6838f:	movups %xmm6,0x0(%r13)
   68394:	mov    0x10(%r14),%rax
   68398:	lea    -0xa0(%rbp),%r14
   6839f:	movq   $0x0,-0x70(%rbp)
   683a7:	mov    %rax,0x10(%r13)
   683ab:	movaps %xmm6,-0x100(%rbp)
   683b2:	movaps %xmm0,-0xa0(%rbp)
   683b9:	movaps %xmm0,-0x80(%rbp)
   683bd:	call   10aa0 <operator new(unsigned long)@plt>
   683c2:	sub    $0x8,%rsp
   683c6:	mov    %r15,%r8
   683c9:	mov    %r14,%rcx
   683cc:	mov    %rax,%rdi
   683cf:	movsd  -0xe0(%rbp),%xmm0
   683d7:	lea    0x223552(%rip),%r9        # 28b930 <OrthoSys::O>
   683de:	mov    %rax,%r12
   683e1:	movapd %xmm0,%xmm4
   683e5:	unpcklpd %xmm4,%xmm4
   683e9:	movaps %xmm4,-0x100(%rbp)
   683f0:	push   %r9
   683f2:	movsd  -0xe8(%rbp),%xmm1
   683fa:	mov    -0xf0(%rbp),%rdx
   68401:	mov    -0x104(%rbp),%esi
   68407:	call   67550 <DEM::Particle::Particle(int, Array<blitz::TinyVector<double, 3> > const&, Array<Array<int> > const&, Array<Array<int> > const&, blitz::TinyVector<double, 3> const&, blitz::TinyVector<double, 3> const&, double, double)>
   6840c:	pop    %rax
   6840d:	mov    0x120(%rbx),%rsi
   68414:	pop    %rdx
   68415:	mov    %r12,-0xc8(%rbp)
   6841c:	cmp    0x128(%rbx),%rsi
   68423:	je     68560 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x270>
   68429:	mov    %r12,(%rsi)
   6842c:	add    $0x8,%rsi
   68430:	mov    %rsi,0x120(%rbx)
   68437:	mov    0x120(%rbx),%rax
   6843e:	movq   0xc090a(%rip),%xmm0        # 128d50 <cuda::std::ranges::__4::__cpo::swap+0x7e>
   68446:	pxor   %xmm2,%xmm2
   6844a:	movsd  -0xe8(%rbp),%xmm1
   68452:	mulsd  0xc0c26(%rip),%xmm1        # 129080 <libcudart_static_71f028fdd4617209d54f8c1be3ec8f7a667e1384+0x30>
   6845a:	movaps %xmm2,-0x50(%rbp)
   6845e:	mov    %rax,%rdx
   68461:	movaps %xmm0,-0x60(%rbp)
   68465:	mov    -0x8(%rax),%rax
   68469:	movdqa 0xc08df(%rip),%xmm0        # 128d50 <cuda::std::ranges::__4::__cpo::swap+0x7e>
   68471:	mulsd  0xc0be7(%rip),%xmm1        # 129060 <libcudart_static_71f028fdd4617209d54f8c1be3ec8f7a667e1384+0x10>
   68479:	sub    0x118(%rbx),%rdx
   68480:	movups %xmm0,0x1c0(%rax)
   68487:	pxor   %xmm0,%xmm0
   6848b:	movsd  -0xe0(%rbp),%xmm3
   68493:	movapd -0x100(%rbp),%xmm5
   6849b:	movups %xmm0,0x1d0(%rax)
   684a2:	movsd  0xc0c2e(%rip),%xmm0        # 1290d8 <libcudart_static_71f028fdd4617209d54f8c1be3ec8f7a667e1384+0x88>
   684aa:	mov    -0x110(%rbp),%rcx
   684b1:	sar    $0x3,%rdx
   684b5:	sub    $0x1,%rdx
   684b9:	mulsd  %xmm3,%xmm0
   684bd:	mulsd  %xmm3,%xmm1
   684c1:	unpcklpd %xmm1,%xmm0
   684c5:	mulpd  %xmm5,%xmm0
   684c9:	mulpd  %xmm5,%xmm0
   684cd:	movups %xmm0,0x290(%rax)
   684d4:	unpckhpd %xmm0,%xmm0
   684d8:	mulsd  0xc0928(%rip),%xmm0        # 128e08 <cuda::std::ranges::__4::__cpo::swap+0x136>
   684e0:	mulsd  %xmm3,%xmm0
   684e4:	mulsd  %xmm3,%xmm0
   684e8:	movapd %xmm0,%xmm1
   684ec:	movsd  %xmm0,0x158(%rax)
   684f4:	unpcklpd %xmm1,%xmm1
   684f8:	movups %xmm1,0x148(%rax)
   684ff:	movdqu (%rcx),%xmm6
   68503:	movups %xmm6,0x28(%rax)
   68507:	mov    0x10(%rcx),%rcx
   6850b:	movb   $0x1,0x1c(%rax)
   6850f:	mov    %rcx,0x38(%rax)
   68513:	mov    %rdx,0x8(%rax)
   68517:	movaps %xmm6,-0xe0(%rbp)
   6851e:	movups %xmm2,0x1e0(%rax)
   68525:	movsd  %xmm3,0x1f0(%rax)
   6852d:	mov    -0x38(%rbp),%rax
   68531:	sub    %fs:0x28,%rax
   6853a:	jne    685b0 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x2c0>
   6853c:	mov    -0xb0(%rbp),%rsi
   68543:	lea    -0x28(%rbp),%rsp
   68547:	mov    %r13,%rdi
   6854a:	pop    %rbx
   6854b:	pop    %r12
   6854d:	sub    %r13,%rsi
   68550:	pop    %r13
   68552:	pop    %r14
   68554:	pop    %r15
   68556:	pop    %rbp
   68557:	jmp    100d0 <operator delete(void*, unsigned long)@plt>
   6855c:	nopl   0x0(%rax)
   68560:	lea    -0xc8(%rbp),%rdx
   68567:	lea    0x118(%rbx),%rdi
   6856e:	call   68160 <void std::vector<DEM::Particle*, std::allocator<DEM::Particle*> >::_M_realloc_insert<DEM::Particle* const&>(__gnu_cxx::__normal_iterator<DEM::Particle**, std::vector<DEM::Particle*, std::allocator<DEM::Particle*> > >, DEM::Particle* const&)>
   68573:	jmp    68437 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x147>
   68578:	mov    $0x360,%esi
   6857d:	mov    %r12,%rdi
   68580:	call   100d0 <operator delete(void*, unsigned long)@plt>
   68585:	mov    %r15,%rdi
   68588:	call   56c90 <std::vector<Array<int>, std::allocator<Array<int> > >::~vector()>
   6858d:	mov    %r14,%rdi
   68590:	call   56c90 <std::vector<Array<int>, std::allocator<Array<int> > >::~vector()>
   68595:	mov    -0xf0(%rbp),%rdi
   6859c:	call   56c60 <std::vector<blitz::TinyVector<double, 3>, std::allocator<blitz::TinyVector<double, 3> > >::~vector()>
   685a1:	mov    -0x38(%rbp),%rax
   685a5:	sub    %fs:0x28,%rax
   685ae:	je     685d0 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x2e0>
   685b0:	call   10260 <__stack_chk_fail@plt>
   685b5:	endbr64
   685b9:	mov    %rax,%rbx
   685bc:	jmp    68578 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x288>
   685be:	endbr64
   685c2:	mov    %rax,%rbx
   685c5:	jmp    68585 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x295>
   685c7:	endbr64
   685cb:	mov    %rax,%rbx
   685ce:	jmp    68595 <DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)+0x2a5>
   685d0:	mov    %rbx,%rdi
   685d3:	call   105b0 <_Unwind_Resume@plt>
   685d8:	nopl   0x0(%rax,%rax,1)

